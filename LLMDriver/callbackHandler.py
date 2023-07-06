from typing import Any, Dict, List, Optional
from uuid import UUID
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish
from collections import defaultdict
from rich import print


class CustomHandler(BaseCallbackHandler):
    def __init__(self) -> None:
        super().__init__()
        self.memory: list[str] = []

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""
        pass
        # print("serialized",serialized)
        # print("prompts",prompts)

    def on_agent_finish(
        self, finish: AgentFinish, *, run_id: UUID,
        parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        self.memory.append(finish.log)
        print("agent finished")
        return super().on_agent_finish(
            finish, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_agent_action(
        self, action: AgentAction, *, run_id: UUID,
        parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> Any:
        self.memory.append(action.log)
        # print(action.tool, end='->')
        return super().on_agent_action(
            action, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""
        self.memory[-1] += 'Observation: ' + output + '\n'
        return super().on_tool_end(output, **kwargs)


class reflectionHandler(BaseCallbackHandler):
    def __init__(self) -> None:
        super().__init__()
        self.memory: list[str] = []

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        print('on_llm_start', prompts)

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], *, run_id: UUID, parent_run_id: UUID, tags: List[str], **kwargs: Any) -> Any:
        print('on_chain_start: ', inputs)
