"""Message processor that handles message processing logic."""

import re
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

from .models import Context, Response, Message
from utils.logger import LoggerMixin
from utils.event_bus import publish_event

if TYPE_CHECKING:
    from llm.llm_manager import LLMManager
    from mcp.mcp_manager import MCPManager


class MessageProcessor(LoggerMixin):
    """Message processor that handles message processing logic."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the message processor."""
        self.config = config
        self.mcp_keywords = config.get("mcp_keywords", [
            "file", "directory", "list", "read", "write", "delete", "create",
            "search", "find", "execute", "run", "command", "system", "process",
            "database", "query", "sql", "api", "http", "request", "fetch"
        ])
        self.llm_keywords = config.get("llm_keywords", [
            "explain", "help", "how", "what", "why", "when", "where", "who",
            "analyze", "summarize", "translate", "generate", "create", "write",
            "answer", "question", "discuss", "describe", "compare", "contrast"
        ])
        self.max_context_length = config.get("max_context_length", 4000)
        self.enable_mcp_fallback = config.get("enable_mcp_fallback", True)
        
    async def process_message(
        self, 
        context: Context, 
        llm_manager: Optional['LLMManager'] = None,
        mcp_manager: Optional['MCPManager'] = None
    ) -> Response:
        """Process a message and return a response."""
        try:
            # Analyze the message to determine processing strategy
            strategy = self._determine_processing_strategy(context)
            
            self.logger.info(f"Processing message with strategy: {strategy}")
            
            # Process based on strategy
            if strategy == "mcp_only":
                return await self._process_with_mcp(context, mcp_manager)
            elif strategy == "llm_only":
                return await self._process_with_llm(context, llm_manager)
            elif strategy == "hybrid":
                return await self._process_hybrid(context, llm_manager, mcp_manager)
            else:
                # Default to LLM
                return await self._process_with_llm(context, llm_manager)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            
            # Return error response
            return Response(
                content=f"I apologize, but I encountered an error while processing your message: {str(e)}",
                status="error",
                metadata={"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            )
    
    def _determine_processing_strategy(self, context: Context) -> str:
        """Determine the processing strategy based on message content and context."""
        message = context.message.lower()
        
        # Check for explicit MCP requests
        if self._is_mcp_request(message):
            return "mcp_only"
        
        # Check for explicit LLM requests
        if self._is_llm_request(message):
            return "llm_only"
        
        # Check for hybrid requests (both LLM and MCP needed)
        if self._is_hybrid_request(message):
            return "hybrid"
        
        # Check for MCP keywords
        if self._contains_mcp_keywords(message):
            return "mcp_only"
        
        # Check for LLM keywords
        if self._contains_llm_keywords(message):
            return "llm_only"
        
        # Default to LLM for general conversation
        return "llm_only"
    
    def _is_mcp_request(self, message: str) -> bool:
        """Check if the message is an explicit MCP request."""
        mcp_patterns = [
            r"\b(list|show|get)\s+(files?|directories?|processes?)\b",
            r"\b(read|open|view)\s+(file|document)\b",
            r"\b(create|make|new)\s+(file|directory|folder)\b",
            r"\b(delete|remove|rm)\s+(file|directory)\b",
            r"\b(run|execute|start)\s+(command|program|script)\b",
            r"\b(search|find)\s+(in|for)\b",
            r"\b(query|select)\s+(database|db)\b"
        ]
        
        for pattern in mcp_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def _is_llm_request(self, message: str) -> bool:
        """Check if the message is an explicit LLM request."""
        llm_patterns = [
            r"\b(explain|describe|tell me about)\b",
            r"\b(how|what|why|when|where|who)\b",
            r"\b(analyze|summarize|review)\b",
            r"\b(translate|convert)\b",
            r"\b(generate|create|write)\s+(text|story|poem|essay)\b",
            r"\b(help|assist|guide)\b"
        ]
        
        for pattern in llm_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def _is_hybrid_request(self, message: str) -> bool:
        """Check if the message requires both LLM and MCP processing."""
        hybrid_patterns = [
            r"\b(analyze|examine|review)\s+(file|document|data)\b",
            r"\b(explain|describe)\s+(what|how)\s+(file|process|system)\b",
            r"\b(help me understand|show me)\s+(file|data|output)\b"
        ]
        
        for pattern in hybrid_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def _contains_mcp_keywords(self, message: str) -> bool:
        """Check if the message contains MCP-related keywords."""
        return any(keyword in message for keyword in self.mcp_keywords)
    
    def _contains_llm_keywords(self, message: str) -> bool:
        """Check if the message contains LLM-related keywords."""
        return any(keyword in message for keyword in self.llm_keywords)
    
    async def _process_with_mcp(
        self, 
        context: Context, 
        mcp_manager: Optional['MCPManager']
    ) -> Response:
        """Process message using MCP servers only."""
        if not mcp_manager:
            return Response(
                content="I'm sorry, but MCP functionality is not available at the moment.",
                status="error",
                metadata={"error": "MCP manager not available"}
            )
        
        try:
            # Extract tool name and arguments from message
            tool_name, arguments = self._extract_mcp_request(context.message)
            
            # Call MCP tool
            result = await mcp_manager.call_tool(tool_name, arguments)
            
            # Format response
            content = self._format_mcp_response(result)
            
            return Response(
                content=content,
                status="success",
                metadata={
                    "processing_strategy": "mcp_only",
                    "tool_used": tool_name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing with MCP: {e}")
            
            # Try fallback to LLM if enabled
            if self.enable_mcp_fallback:
                return Response(
                    content=f"I tried to process your request but encountered an issue: {str(e)}. Let me try to help you with a general response.",
                    status="partial",
                    metadata={"error": str(e), "fallback": True}
                )
            else:
                return Response(
                    content=f"I'm sorry, but I couldn't process your request: {str(e)}",
                    status="error",
                    metadata={"error": str(e)}
                )
    
    async def _process_with_llm(
        self, 
        context: Context, 
        llm_manager: Optional['LLMManager']
    ) -> Response:
        """Process message using LLM only."""
        if not llm_manager:
            return Response(
                content="I'm sorry, but LLM functionality is not available at the moment.",
                status="error",
                metadata={"error": "LLM manager not available"}
            )
        
        try:
            # Prepare messages for LLM
            messages = self._prepare_messages_for_llm(context)
            
            # Generate response
            content = await llm_manager.generate_response(messages, context)
            
            return Response(
                content=content,
                status="success",
                metadata={
                    "processing_strategy": "llm_only",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing with LLM: {e}")
            return Response(
                content=f"I'm sorry, but I encountered an error while processing your message: {str(e)}",
                status="error",
                metadata={"error": str(e)}
            )
    
    async def _process_hybrid(
        self, 
        context: Context, 
        llm_manager: Optional['LLMManager'],
        mcp_manager: Optional['MCPManager']
    ) -> Response:
        """Process message using both LLM and MCP."""
        try:
            # First, use MCP to get data/information
            mcp_response = await self._process_with_mcp(context, mcp_manager)
            
            if mcp_response.status == "error":
                # Fallback to LLM only
                return await self._process_with_llm(context, llm_manager)
            
            # Then, use LLM to analyze/explain the results
            enhanced_context = context.copy()
            enhanced_context.message = f"Based on this information: {mcp_response.content}\n\nPlease analyze and explain: {context.message}"
            
            llm_response = await self._process_with_llm(enhanced_context, llm_manager)
            
            return Response(
                content=llm_response.content,
                status="success",
                metadata={
                    "processing_strategy": "hybrid",
                    "mcp_tool_used": mcp_response.metadata.get("tool_used"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing hybrid request: {e}")
            # Fallback to LLM only
            return await self._process_with_llm(context, llm_manager)
    
    def _extract_mcp_request(self, message: str) -> tuple[str, Dict[str, Any]]:
        """Extract tool name and arguments from message."""
        # Simple extraction logic - can be enhanced
        message_lower = message.lower()
        
        # Default tool and arguments
        tool_name = "list_files"
        arguments = {"path": "."}
        
        # Extract based on patterns
        if "list" in message_lower and ("file" in message_lower or "directory" in message_lower):
            tool_name = "list_files"
            # Extract path if specified - look for specific directory patterns
            path_match = re.search(r"in\s+(the\s+)?([^\s]+(?:\s+[^\s]+)*?)(?:\s+directory)?", message_lower)
            if path_match:
                path = path_match.group(2)  # Get the actual path, not "the"
                # Handle common cases
                if path in ["current", "this", "here"]:
                    arguments["path"] = "."
                else:
                    arguments["path"] = path
        
        elif "read" in message_lower and "file" in message_lower:
            tool_name = "read_file"
            # Extract filename
            file_match = re.search(r"read\s+([^\s]+)", message_lower)
            if file_match:
                arguments["path"] = file_match.group(1)
        
        elif "search" in message_lower:
            tool_name = "search_files"
            # Extract search term - handle various patterns
            search_patterns = [
                r"search\s+for\s+([^\s]+)",
                r"search\s+([^\s]+)",
                r"find\s+files\s+containing\s+([^\s]+)",
                r"find\s+([^\s]+)\s+files"
            ]
            
            for pattern in search_patterns:
                search_match = re.search(pattern, message_lower)
                if search_match:
                    search_term = search_match.group(1)
                    # Convert to glob pattern
                    if "test" in search_term:
                        arguments["pattern"] = "*test*"
                        arguments["recursive"] = True
                    elif "py" in search_term:
                        arguments["pattern"] = "*.py"
                        arguments["recursive"] = True
                    else:
                        arguments["pattern"] = f"*{search_term}*"
                        arguments["recursive"] = True
                    break
        
        return tool_name, arguments
    
    def _format_mcp_response(self, result: Dict[str, Any]) -> str:
        """Format MCP response for user consumption."""
        if "content" in result:
            return result["content"]
        elif "files" in result:
            files = result["files"]
            if isinstance(files, list):
                if len(files) == 0:
                    return "No files found."
                elif len(files) <= 10:
                    return f"Found {len(files)} files:\n" + "\n".join(f"- {f.get('name', f)} ({f.get('type', 'unknown')})" for f in files)
                else:
                    return f"Found {len(files)} files. Showing first 10:\n" + "\n".join(f"- {f.get('name', f)} ({f.get('type', 'unknown')})" for f in files[:10]) + f"\n... and {len(files) - 10} more files"
            else:
                return str(files)
        elif "data" in result:
            return str(result["data"])
        else:
            return str(result)
    
    def _prepare_messages_for_llm(self, context: Context) -> List[Message]:
        """Prepare messages for LLM processing."""
        messages = []
        
        # Add system message if available
        if context.metadata and "system_prompt" in context.metadata:
            messages.append(Message(
                content=context.metadata["system_prompt"],
                role="system"
            ))
        
        # Add conversation history (limited by max_context_length)
        total_length = 0
        for message in reversed(context.message_history):
            message_length = len(message.content)
            if total_length + message_length > self.max_context_length:
                break
            messages.insert(0, message)
            total_length += message_length
        
        # Add current message
        messages.append(Message(
            content=context.message,
            role="user"
        ))
        
        return messages 