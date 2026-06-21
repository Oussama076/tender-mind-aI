"""ADK Orchestrator for TenderMind AI.

Coordinates the multi-agent swarm consisting of Analyst, Strategy,
Legal, and Bid Writer agents using the Google GenAI SDK.
"""

import logging
import time
from google import genai
from google.genai import types
import chromadb
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception
from typing import Any, Dict, List, Optional

from src.agents.skill_loader import load_agent_skill

logger = logging.getLogger(__name__)

DB_PATH = "data/db"
COLLECTION_NAME = "rfp_documents"
CORPORATE_COLLECTION_NAME = "corporate_knowledge"


def is_retryable_error(exception: Exception) -> bool:
    """Helper to detect retryable transient errors from the Gemini API.
    
    Args:
        exception: The encountered exception.
        
    Returns:
        bool: True if it is a transient/rate-limiting error, False otherwise.
    """
    err_str = str(exception)
    return "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "503" in err_str


@retry(
    wait=wait_exponential(multiplier=1.5, min=10, max=60),
    stop=stop_after_attempt(7),
    retry=retry_if_exception(is_retryable_error)
)
def send_message_with_retry(chat: Any, message: Any) -> Any:
    """Wrapper to send a chat message with exponential backoff on transient failures."""
    logger.info("Sending message to Gemini...")
    return chat.send_message(message)


@retry(
    wait=wait_exponential(multiplier=1.5, min=10, max=60),
    stop=stop_after_attempt(7),
    retry=retry_if_exception(is_retryable_error)
)
def generate_content_with_retry(client: Any, model: str, contents: Any, config: Optional[Any] = None) -> Any:
    """Wrapper to call generate_content with exponential backoff on transient failures."""
    logger.info("Generating content with Gemini...")
    return client.models.generate_content(model=model, contents=contents, config=config)


def search_rfp_database(query: str, rfp_id: Optional[str] = None) -> str:
    """Queries the local ChromaDB for RFP context using the text-embedding-004 model.
    
    Args:
        query: Search string.
        rfp_id: Optional RFP document ID to filter query results.
        
    Returns:
        str: Concatenated matching document chunks or a failure message.
    """
    try:
        client = genai.Client()
        response = client.models.embed_content(
            model='gemini-embedding-2',
            contents=query
        )
        query_embedding = response.embeddings[0].values
        
        chroma_client = chromadb.PersistentClient(path=DB_PATH)
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
        
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": 3
        }
        
        if rfp_id:
            kwargs["where"] = {"doc_id": rfp_id}
            
        results = collection.query(**kwargs)
        
        if results and "documents" in results and results["documents"]:
            return "\n\n".join(results["documents"][0])
        return "No relevant information found in the database."
    except Exception as e:
        logger.error(f"Error querying database: {e}")
        return f"Database query failed: {e}"


def search_corporate_memory(query: str) -> str:
    """Queries the Corporate Knowledge ChromaDB collection using text-embedding-004.
    
    Args:
        query: Search string.
        
    Returns:
        str: Concatenated corporate capability matches or a failure message.
    """
    try:
        client = genai.Client()
        response = client.models.embed_content(
            model='gemini-embedding-2',
            contents=query
        )
        query_embedding = response.embeddings[0].values
        
        chroma_client = chromadb.PersistentClient(path=DB_PATH)
        collection = chroma_client.get_collection(name=CORPORATE_COLLECTION_NAME)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        if results and "documents" in results and results["documents"]:
            return "\n\n".join(results["documents"][0])
        return "No relevant corporate information found in the memory database."
    except Exception as e:
        logger.error(f"Error querying corporate memory: {e}")
        return f"Corporate database query failed: {e}"


class ADKOrchestrator:
    """Orchestrator managing multi-agent execution state and Human-In-The-Loop handoffs.
    
    Attributes:
        client: The Gemini client SDK instance.
        rfp_id: Target RFP ID to scope RAG queries.
        state: Shared swarm execution state containing outputs from all agents.
    """
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None, rfp_id: Optional[str] = None) -> None:
        """Initializes the orchestrator with state and optional target RFP ID."""
        self.client = genai.Client()
        self.rfp_id = rfp_id
        self.state = initial_state or {
            "analyst_output": None,
            "strategy_output": None,
            "legal_output": None,
            "writer_output": None
        }

    def run_analyst_agent(self, initial_query: str) -> str:
        """Runs the Analyst Agent to extract technical deliverables and specifications.
        
        Args:
            initial_query: Core analysis focus query.
            
        Returns:
            str: Markdown list of findings.
        """
        logger.info("Starting Analyst Agent...")
        
        skill = load_agent_skill("analyst")
        model_name = skill.get("parameters", {}).get("model", "gemini-3.1-flash-lite")
        temp = skill.get("parameters", {}).get("temperature", 0.2)
        
        tool_config = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="search_rfp_database",
                    description="Searches the RFP database to retrieve technical specs, mandatory requirements, and evaluation criteria.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "query": types.Schema(
                                type=types.Type.STRING,
                                description="The specific search query"
                            )
                        },
                        required=["query"]
                    )
                )
            ]
        )

        chat = self.client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=skill["instructions"],
                tools=[tool_config],
                temperature=temp
            )
        )
        
        response = send_message_with_retry(
            chat, 
            f"Please extract the core technical specifications and mandatory requirements based on this initial focus area: {initial_query}"
        )
        
        while response.function_calls:
            tool_responses = []
            for function_call in response.function_calls:
                if function_call.name == "search_rfp_database":
                    query_arg = function_call.args.get("query", initial_query)
                    tool_result_text = search_rfp_database(query_arg, rfp_id=self.rfp_id)
                    
                    tool_response = types.Part.from_function_response(
                        name="search_rfp_database",
                        response={"result": tool_result_text}
                    )
                    tool_responses.append(tool_response)
            
            if tool_responses:
                response = send_message_with_retry(chat, tool_responses)
            else:
                break
        
        self.state["analyst_output"] = response.text
        return response.text

    def run_strategy_agent(self) -> str:
        """Runs the Strategy Agent to map analyst findings against corporate capabilities.
        
        Returns:
            str: Evaluation of alignment against company capabilities.
        """
        logger.info("Starting Strategy Agent...")
        if not self.state["analyst_output"]:
            raise ValueError("Analyst Agent must run before Strategy Agent.")
            
        skill = load_agent_skill("strategy")
        model_name = skill.get("parameters", {}).get("model", "gemini-3.1-flash-lite")
        temp = skill.get("parameters", {}).get("temperature", 0.3)
        
        tool_config = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="search_corporate_memory",
                    description="Searches the corporate knowledge base to find relevant company history, capabilities, and past projects.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "query": types.Schema(
                                type=types.Type.STRING,
                                description="The specific corporate information to search for"
                            )
                        },
                        required=["query"]
                    )
                )
            ]
        )
        
        chat = self.client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=skill["instructions"],
                tools=[tool_config],
                temperature=temp
            )
        )
        
        prompt = f"Analyst Technical Findings:\n\n{self.state['analyst_output']}\n\nPlease evaluate this against our corporate capabilities."
        response = send_message_with_retry(chat, prompt)
        
        while response.function_calls:
            tool_responses = []
            for function_call in response.function_calls:
                if function_call.name == "search_corporate_memory":
                    query_arg = function_call.args.get("query", "")
                    tool_result_text = search_corporate_memory(query_arg)
                    
                    tool_response = types.Part.from_function_response(
                        name="search_corporate_memory",
                        response={"result": tool_result_text}
                    )
                    tool_responses.append(tool_response)
            
            if tool_responses:
                response = send_message_with_retry(chat, tool_responses)
            else:
                break
                
        self.state["strategy_output"] = response.text
        return response.text

    def run_legal_agent(self) -> str:
        """Runs the Legal Agent to audit compliance risks, penalties, and mitigations.
        
        Returns:
            str: Risk report and mitigations.
        """
        logger.info("Starting Legal Agent...")
        if not self.state["analyst_output"]:
            raise ValueError("Analyst Agent must run before Legal Agent.")
            
        skill = load_agent_skill("legal")
        model_name = skill.get("parameters", {}).get("model", "gemini-3.1-flash-lite")
        temp = skill.get("parameters", {}).get("temperature", 0.3)
        
        prompt = f"Analyst Findings to Review:\n\n{self.state['analyst_output']}"
        
        response = generate_content_with_retry(
            client=self.client,
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=skill["instructions"],
                temperature=temp
            )
        )
        self.state["legal_output"] = response.text
        return response.text

    def run_bid_writer_agent(self) -> str:
        """Runs the Bid Writer Agent to compile findings into the final proposal draft.
        
        Returns:
            str: Structured drafted proposal.
        """
        logger.info("Starting Bid Writer Agent...")
        if not self.state["analyst_output"] or not self.state["legal_output"]:
            raise ValueError("Analyst and Legal Agents must run before Bid Writer Agent.")
            
        skill = load_agent_skill("writer")
        model_name = skill.get("parameters", {}).get("model", "gemini-3.1-flash-lite")
        temp = skill.get("parameters", {}).get("temperature", 0.7)
        
        tool_config = types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="search_corporate_memory",
                    description="Searches the corporate knowledge base to find relevant company history, methodologies, pricing, and past proposals.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "query": types.Schema(
                                type=types.Type.STRING,
                                description="The specific corporate information to search for"
                            )
                        },
                        required=["query"]
                    )
                )
            ]
        )
        
        chat = self.client.chats.create(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=skill["instructions"],
                tools=[tool_config],
                temperature=temp
            )
        )
            
        prompt = (
            f"Analyst Technical Findings:\n{self.state['analyst_output']}\n\n"
            f"Legal and Compliance Review:\n{self.state['legal_output']}\n\n"
            f"Please draft the final proposal. Use your search_corporate_memory tool to fill in details."
        )
        
        response = send_message_with_retry(chat, prompt)
        
        while response.function_calls:
            tool_responses = []
            for function_call in response.function_calls:
                if function_call.name == "search_corporate_memory":
                    query_arg = function_call.args.get("query", "")
                    tool_result_text = search_corporate_memory(query_arg)
                    
                    tool_response = types.Part.from_function_response(
                        name="search_corporate_memory",
                        response={"result": tool_result_text}
                    )
                    tool_responses.append(tool_response)
            
            if tool_responses:
                response = send_message_with_retry(chat, tool_responses)
            else:
                break
                    
        self.state["writer_output"] = response.text
        return response.text

    def execute_pre_review_pipeline(self, focus_area: str) -> Dict[str, Any]:
        """Executes the pre-review segment of the pipeline (Analyst -> Strategy -> Legal).
        
        Args:
            focus_area: The focus target area.
            
        Returns:
            Dict[str, Any]: Current execution state with intermediate agent outputs.
        """
        logger.info("--- ADK Pre-Review Pipeline Started ---")
        self.run_analyst_agent(focus_area)
        self.run_strategy_agent()
        self.run_legal_agent()
        logger.info("--- ADK Pre-Review Pipeline Complete (Waiting for Human) ---")
        return self.state

    def execute_post_review_pipeline(self) -> Dict[str, Any]:
        """Executes the final post-review segment of the pipeline (Bid Writer).
        
        Returns:
            Dict[str, Any]: Updated execution state with final writer output.
        """
        logger.info("--- ADK Post-Review Pipeline Started ---")
        self.run_bid_writer_agent()
        logger.info("--- ADK Post-Review Pipeline Complete ---")
        return self.state
