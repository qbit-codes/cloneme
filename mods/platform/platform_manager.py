"""
Platform Manager for Unified AI Logic

This module contains the shared AI logic that works across all platforms.
It handles message processing, decision making, and response generation
using platform-agnostic Message, Person, and Chat objects.
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from langchain_core.language_models.chat_models import BaseChatModel

from mods.agent.decisions.decision import Decision
from mods.agent.response_generator import ResponseGenerator
from mods.objects.messages.Message import Message
from mods.objects.person.Person import Person
from mods.utils.logging_config import LoggingConfig
from mods.utils.message_utils import format_message_content_with_truncation, get_sender_display_name, is_ai_message

if TYPE_CHECKING:
    from mods.config import Profile, SettingsManager
    from mods.agent.tools.tool import ToolCall
    from mods.platform.base_platform import BasePlatform


class PlatformManager:
    """
    Unified AI logic manager that works across all social media platforms.
    
    This class contains all the AI decision making, response generation, and message
    processing logic that is platform-independent. Platform-specific implementations
    delegate their AI logic to this manager.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        profile: Optional["Profile"] = None,
        settings_manager: Optional["SettingsManager"] = None
    ):
        """
        Initialize the platform manager with AI components.

        Args:
            llm (BaseChatModel): The language model for AI operations.
            profile (Optional[Profile]): The profile to use for the bot.
            settings_manager (Optional[SettingsManager]): The settings manager for hot-reloadable configuration.
        """
        self.llm = llm
        self.profile = profile
        self.settings_manager = settings_manager
        self.decision = Decision(llm=llm, profile=profile, settings_manager=settings_manager)
        self.response_generator = ResponseGenerator(llm=llm, profile=profile, decision_engine=self.decision, settings_manager=settings_manager)
        self.logger = LoggingConfig.get_logger("platform_manager")

    async def process_message(
        self,
        platform: "BasePlatform",
        message: Message,
        context_messages: List[Message],
        is_dm_override: Optional[bool] = None
    ) -> bool:
        """
        Process a message using unified AI logic across all platforms.

        Args:
            platform (BasePlatform): The platform instance that received the message.
            message (Message): The message to process.
            context_messages (List[Message]): Recent messages for context.

        Returns:
            bool: True if a response was sent, False otherwise.
        """
        try:
            sender = message.sender
            chat_id = message.chat.chat_id

            sender_type = "AI" if is_ai_message(message) else "USER"
            sender_display = get_sender_display_name(message, include_ai_indicator=True)
            self.logger.debug(
                f"🔄 Processing {sender_type} message from {sender_display} [{sender.person_id}][{sender.identifiers}] in chat {chat_id} on {platform.get_platform_name()}..."
            )

            # Use AI to make reply decision
            (
                should_reply,
                reasoning,
                is_flagged,
                flagged_line,
            ) = self.decision.should_reply(
                target_message=message,
                context_messages=context_messages,
                person=sender,
                is_dm_override=is_dm_override,
            )

            formatted_reasoning = format_message_content_with_truncation(reasoning, 500, False)
            formatted_reasoning = formatted_reasoning.replace("\n", "\n     ")

            # Handle flagged content
            if is_flagged:
                return await self._handle_flagged_content(
                    platform, message, flagged_line, formatted_reasoning
                )

            # Handle normal reply logic
            if should_reply:
                return await self._handle_reply(
                    platform, message, context_messages, formatted_reasoning
                )
            else:
                return await self._handle_no_reply(
                    platform, message, formatted_reasoning
                )

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return False

    async def _handle_flagged_content(
        self,
        platform: "BasePlatform",
        message: Message,
        flagged_line: Optional[str],
        reasoning: str
    ) -> bool:
        """Handle flagged content according to profile settings."""
        sender = message.sender
        chat_id = message.chat.chat_id

        self.logger.debug(
            f"🚩 FLAGGED content detected from [{sender.person_id}][{sender.identifiers}] in chat {chat_id}"
        )

        if flagged_line:
            platform.add_flagged_message(message.message_id, chat_id, flagged_line)
            # Show the flagged content (which should now be the actual message content)
            formatted_flagged = format_message_content_with_truncation(flagged_line, 100, True)
            self.logger.debug(f"   🔍 Flagged Content: {formatted_flagged}")
        else:
            self.logger.debug(f"   🔍 Flagged Content: [No specific content identified]")

        formatted_message = format_message_content_with_truncation(message.content, 100, True)
        self.logger.debug(f"   📝 Message: {formatted_message}")
        self.logger.debug(f"   🤔 Reasoning: {reasoning}")

        # Check if profile allows responses to flagged content
        if self.profile and self.profile.should_reply_to_off_topic():
            self.logger.debug("   ✅ Profile allows responses to flagged content - generating response")

            try:
                off_topic_guidance = self.profile.get_off_topic_guidance()
                context_messages = await platform.collect_context(message, 10)

                generated_response, security_breach = await self.response_generator.generate_response(
                    target_message=message,
                    person=sender,
                    intent="basic",
                    context_messages=context_messages,
                    tool_results=None,
                    relevant_memories=None,
                    extra_context=f"FLAGGED CONTENT RESPONSE: {off_topic_guidance}",
                )

                if generated_response:
                    success = await self._send_response_with_typing(
                        platform, chat_id, generated_response
                    )
                    if success:
                        formatted_response = format_message_content_with_truncation(generated_response, 150, True)
                        self.logger.debug(f"   💬 Flagged Response Sent: {formatted_response}")
                        return True
                else:
                    self.logger.debug("   ❌ No response generated for flagged content")

            except Exception as e:
                self.logger.error(f"   ❌ Error generating flagged content response: {e}")
        else:
            self.logger.debug("   ❌ Profile settings: Do not respond to flagged content")

        self.logger.debug(f"   ⏰ Timestamp: {message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self.logger.debug("-" * 80)
        return False

    async def _handle_reply(
        self,
        platform: "BasePlatform",
        message: Message,
        context_messages: List[Message],
        reasoning: str
    ) -> bool:
        """Handle normal reply generation and sending."""
        sender = message.sender
        chat_id = message.chat.chat_id

        sender_type = "AI" if is_ai_message(message) else "USER"
        sender_display = get_sender_display_name(message, include_ai_indicator=True)
        self.logger.debug(
            f"✅ AI WILL REPLY to {sender_type} message from {sender_display} [{sender.person_id}][{sender.identifiers}] in chat {chat_id}"
        )
        formatted_message = format_message_content_with_truncation(message.content, 100, True)
        self.logger.debug(f"   📝 Message: {formatted_message}")
        self.logger.debug(f"   🤔 Reasoning: {reasoning}")

        # Detect intention
        intent, intent_reasoning = self.decision.detect_intention(
            target_message=message,
            person=sender,
            context_messages=context_messages,
        )

        formatted_intent_reasoning = format_message_content_with_truncation(intent_reasoning, 300, False)
        formatted_intent_reasoning = formatted_intent_reasoning.replace("\n", "\n     ")

        self.logger.debug(f"   🎯 Intent: <intent>{intent}</intent>")
        self.logger.debug(f"   💭 Intent Reasoning: {formatted_intent_reasoning}")

        # Detect required tools
        required_tools, tool_reasoning = self.decision.detect_required_tools(
            target_message=message,
            person=sender,
            context_messages=context_messages,
        )

        formatted_tool_reasoning = format_message_content_with_truncation(tool_reasoning, 300, False)
        formatted_tool_reasoning = formatted_tool_reasoning.replace("\n", "\n     ")

        self.logger.debug(f"   🔧 Required Tools: {len(required_tools)} tool(s)")
        if required_tools:
            for i, tool_call in enumerate(required_tools, 1):
                self.logger.debug(f"     {i}. {tool_call.tool_name}({tool_call.primary_param})")
        self.logger.debug(f"   🔍 Tool Reasoning: {formatted_tool_reasoning}")

        # Execute tools if needed
        tool_results = {}
        if required_tools:
            self.logger.debug(f"   ⚙️ Executing {len(required_tools)} tool(s)...")
            tool_results = await self._execute_tools(required_tools)

            for tool_name, result in tool_results.items():
                if result.get("success", False):
                    result_preview = format_message_content_with_truncation(str(result.get("result", "")), 100, True)
                    self.logger.debug(f"     ✅ {tool_name}: {result_preview}")
                else:
                    self.logger.debug(f"     ❌ {tool_name}: {result.get('error', 'Unknown error')}")

        # Handle memory operations
        await self._handle_memory_operations(message, sender, platform.get_platform_name())

        # Generate and send response
        try:
            self.logger.debug("   🎨 Generating AI response...")

            # Get relevant memories for response generation
            relevant_memories, retrieval_reasoning = self.decision.retrieve_relevant_memories(
                target_message=message, person=sender, platform_prefix=platform.get_platform_name()
            )

            generated_response, security_breach = await self.response_generator.generate_response(
                target_message=message,
                person=sender,
                intent=intent,
                context_messages=context_messages,
                tool_results=tool_results if tool_results else None,
                relevant_memories=relevant_memories if relevant_memories else None,
                extra_context=None,
            )

            if security_breach:
                self.logger.debug("   ⚠️ Security breach detected and handled safely")

            if generated_response:
                success = await self._send_response_with_typing(
                    platform, chat_id, generated_response
                )
                if success:
                    formatted_response = format_message_content_with_truncation(generated_response, 150, True)
                    self.logger.debug(f"   💬 Response Sent: {formatted_response}")
                    return True
            else:
                self.logger.debug("   ❌ No response generated")

        except Exception as e:
            self.logger.error(f"   ❌ Error generating response: {e}")
            # Try to send fallback response
            try:
                fallback_response = "I'm having trouble generating a response right now. Please try again!"
                await platform.send_message(chat_id, fallback_response)
                self.logger.debug("   🔄 Sent fallback response")
                return True
            except Exception as fallback_error:
                self.logger.error(f"   ❌ Failed to send fallback response: {fallback_error}")

        return False

    async def _handle_no_reply(
        self,
        platform: "BasePlatform",
        message: Message,
        reasoning: str
    ) -> bool:
        """Handle cases where AI decides not to reply."""
        sender = message.sender
        chat_id = message.chat.chat_id

        sender_type = "AI" if is_ai_message(message) else "USER"
        sender_display = get_sender_display_name(message, include_ai_indicator=True)
        self.logger.debug(f"❌ AI will NOT reply to {sender_type} message from {sender_display} [{sender.person_id}][{sender.identifiers}] in chat {chat_id}")
        formatted_message = format_message_content_with_truncation(message.content, 100, True)
        self.logger.debug(f"   📝 Message: {formatted_message}")
        self.logger.debug(f"   🤔 Reasoning: {reasoning}")
        self.logger.debug(f"   ⏰ Timestamp: {message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Even if not replying, try to save memory if message is not flagged
        self.logger.debug("   💾 Attempting memory analysis despite not replying")
        await self._handle_memory_operations(message, sender, platform.get_platform_name())

        self.logger.debug("-" * 80)
        return False

    async def _handle_memory_operations(
        self,
        message: Message,
        sender: Person,
        platform_name: str
    ) -> None:
        """Handle memory saving and retrieval operations."""
        try:
            memory_saved, memory_reasoning = self.decision.should_save_memory(
                target_message=message,
                person=sender,
                platform_prefix=platform_name
            )

            formatted_memory_reasoning = format_message_content_with_truncation(memory_reasoning, 300, False)
            formatted_memory_reasoning = formatted_memory_reasoning.replace("\n", "\n     ")

            self.logger.debug(f"   💾 Memory Analysis: {'Saved new info' if memory_saved else 'No info to save'}")
            self.logger.debug(f"   🧠 Memory Reasoning: {formatted_memory_reasoning}")

        except Exception as e:
            self.logger.error(f"   ❌ Error in memory operations: {e}")

    async def _send_response_with_typing(
        self,
        platform: "BasePlatform",
        chat_id: str,
        response: str
    ) -> bool:
        """Send a response with realistic typing simulation."""
        try:
            typing_delay = self._calculate_typing_delay(response)
            self.logger.debug(f"   ⌨️ Simulating typing for {typing_delay:.1f} seconds...")

            # Start typing indicator
            await platform.start_typing(chat_id)

            # Wait for typing delay
            await asyncio.sleep(typing_delay)

            # Send message and stop typing
            success = await platform.send_message(chat_id, response)
            await platform.stop_typing(chat_id)

            if success:
                self.logger.debug(f"   📏 Response Length: {len(response)} characters")
                self.logger.debug(f"   ⏱️ Typing Delay: {typing_delay:.1f}s")

            return success

        except Exception as e:
            self.logger.error(f"   ❌ Error sending response with typing: {e}")
            # Try to send without typing simulation
            try:
                return await platform.send_message(chat_id, response)
            except Exception as fallback_error:
                self.logger.error(f"   ❌ Fallback send also failed: {fallback_error}")
                return False

    def _calculate_typing_delay(self, message: str) -> float:
        """
        Calculate a realistic typing delay based on message length using configurable settings.

        Args:
            message (str): The message to calculate typing time for.

        Returns:
            float: Delay in seconds.
        """
        import random

        # Get typing simulation settings
        if self.settings_manager and self.settings_manager.get('ai_behavior.typing_simulation.enabled', True):
            base_speed_range = self.settings_manager.get('ai_behavior.typing_simulation.base_speed_range', [3.5, 5.0])
            thinking_time_range = self.settings_manager.get('ai_behavior.typing_simulation.thinking_time_range', [0.5, 2.0])
            reading_pause_range = self.settings_manager.get('ai_behavior.typing_simulation.reading_pause_range', [0.3, 1.0])
            min_delay = self.settings_manager.get('ai_behavior.typing_simulation.min_delay_seconds', 0.5)
            max_delay = self.settings_manager.get('ai_behavior.typing_simulation.max_delay_seconds', 15.0)
            thinking_threshold = self.settings_manager.get('ai_behavior.typing_simulation.thinking_threshold_chars', 100)
            reading_threshold = self.settings_manager.get('ai_behavior.typing_simulation.reading_threshold_chars', 50)
        else:
            # Fallback to default values
            base_speed_range = [3.5, 5.0]
            thinking_time_range = [0.5, 2.0]
            reading_pause_range = [0.3, 1.0]
            min_delay = 0.5
            max_delay = 15.0
            thinking_threshold = 100
            reading_threshold = 50

        base_speed = random.uniform(base_speed_range[0], base_speed_range[1])
        char_count = len(message)
        base_delay = char_count / base_speed

        if char_count > thinking_threshold:
            thinking_time = random.uniform(thinking_time_range[0], thinking_time_range[1])
            base_delay += thinking_time

        if char_count < reading_threshold:
            reading_pause = random.uniform(reading_pause_range[0], reading_pause_range[1])
            base_delay += reading_pause

        return max(min_delay, min(max_delay, base_delay))

    async def _execute_tools(self, tool_calls: List["ToolCall"]) -> Dict[str, Any]:
        """
        Execute a list of tool calls and return their results.

        Args:
            tool_calls: List of ToolCall objects to execute

        Returns:
            Dict mapping tool names to their execution results
        """
        try:
            from mods.agent.tools.tool import tool_manager

            results = {}
            for tool_call in tool_calls:
                try:
                    tool_result = tool_manager.execute_tool_call(tool_call)

                    tool_key = tool_call.tool_name
                    counter = 1
                    while tool_key in results:
                        tool_key = f"{tool_call.tool_name}_{counter}"
                        counter += 1

                    results[tool_key] = {
                        'success': tool_result.success,
                        'result': tool_result.result,
                        'error': tool_result.error,
                        'tool_call': tool_result.tool_call.to_dict()
                    }

                except Exception as e:
                    results[tool_call.tool_name] = {
                        'success': False,
                        'result': None,
                        'error': f"Tool execution failed: {str(e)}",
                        'tool_call': tool_call.to_dict() if hasattr(tool_call, 'to_dict') else str(tool_call)
                    }

            return results

        except Exception as e:
            self.logger.error(f"Error executing tools: {e}")
            return {}


__all__ = ["PlatformManager"]
