from typing import Optional, cast

from core.entities.application_entities import ModelConfigEntity
from core.memory.token_buffer_memory import TokenBufferMemory
from core.model_runtime.entities.message_entities import PromptMessage
from core.model_runtime.entities.model_entities import ModelPropertyKey
from core.model_runtime.model_providers.__base.large_language_model import LargeLanguageModel


class PromptTransform:
    def _append_chat_histories(self, memory: TokenBufferMemory,
                               prompt_messages: list[PromptMessage],
                               model_config: ModelConfigEntity) -> list[PromptMessage]:
        if memory:
            rest_tokens = self._calculate_rest_token(prompt_messages, model_config)
            histories = self._get_history_messages_list_from_memory(memory, rest_tokens)
            prompt_messages.extend(histories)

        return prompt_messages

    def _calculate_rest_token(self, prompt_messages: list[PromptMessage], model_config: ModelConfigEntity) -> int:
        rest_tokens = 2000

        model_context_tokens = model_config.model_schema.model_properties.get(ModelPropertyKey.CONTEXT_SIZE)
        if model_context_tokens:
            model_type_instance = model_config.provider_model_bundle.model_type_instance
            model_type_instance = cast(LargeLanguageModel, model_type_instance)

            curr_message_tokens = model_type_instance.get_num_tokens(
                model_config.model,
                model_config.credentials,
                prompt_messages
            )

            max_tokens = 0
            for parameter_rule in model_config.model_schema.parameter_rules:
                if (parameter_rule.name == 'max_tokens'
                        or (parameter_rule.use_template and parameter_rule.use_template == 'max_tokens')):
                    max_tokens = (model_config.parameters.get(parameter_rule.name)
                                  or model_config.parameters.get(parameter_rule.use_template)) or 0

            rest_tokens = model_context_tokens - max_tokens - curr_message_tokens
            rest_tokens = max(rest_tokens, 0)

        return rest_tokens

    def _get_history_messages_from_memory(self, memory: TokenBufferMemory,
                                          max_token_limit: int,
                                          human_prefix: Optional[str] = None,
                                          ai_prefix: Optional[str] = None) -> str:
        """Get memory messages."""
        kwargs = {
            "max_token_limit": max_token_limit
        }

        if human_prefix:
            kwargs['human_prefix'] = human_prefix

        if ai_prefix:
            kwargs['ai_prefix'] = ai_prefix

        return memory.get_history_prompt_text(
            **kwargs
        )

    def _get_history_messages_list_from_memory(self, memory: TokenBufferMemory,
                                               max_token_limit: int) -> list[PromptMessage]:
        """Get memory messages."""
        return memory.get_history_prompt_messages(
            max_token_limit=max_token_limit
        )
