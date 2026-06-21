import logging
from mcp.server.fastmcp import FastMCP
from src.ingestion.drive_client import download_rfp_from_drive

logger = logging.getLogger(__name__)

# Initialize the MCP Server
mcp = FastMCP("Google Drive MCP Server")

@mcp.tool()
def fetch_rfp_document(file_id: str) -> str:
    """
    Downloads an RFP document from Google Drive using the configured Service Account,
    and returns the local file path where it was saved.
    
    Args:
        file_id: The Google Drive File ID of the RFP document.
    """
    logger.info(f"MCP Tool called: fetch_rfp_document for file_id: {file_id}")
    try:
        # Download the file via Service Account
        dest_path = download_rfp_from_drive(file_id)
        return dest_path
    except Exception as e:
        error_msg = f"Error downloading document via MCP: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    # Start the MCP server using standard input/output transport
    mcp.run(transport="stdio")
