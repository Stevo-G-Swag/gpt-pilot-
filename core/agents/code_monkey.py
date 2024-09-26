from os.path import basename

from pydantic import BaseModel, Field

from core.agents.base import BaseAgent
from core.agents.convo import AgentConvo
from core.agents.response import AgentResponse, ResponseType
from core.config import CODE_MONKEY_AGENT_NAME, DESCRIBE_FILES_AGENT_NAME
from core.llm.parser import JSONParser, OptionalCodeBlockParser
from core.log import get_logger

import asyncio

log = get_logger(__name__)


class FileDescription(BaseModel):
    summary: str = Field(
        description="Detailed description summarizing what the file is about, and what the major classes, functions, elements, or other functionality implemented."
    )
    references: list[str] = Field(
        description="List of references the file imports or includes (only files local to the project), where each element specifies the project-relative path of the referenced file, including the file extension."
    )


class CodeMonkey(BaseAgent):
    agent_type = "code-monkey"
    display_name = "Code Monkey"

    async def run(self) -> AgentResponse:
        if self.prev_response and self.prev_response.type == ResponseType.DESCRIBE_FILES:
            return await self.describe_files()
        else:
            return await self.implement_changes()

    async def implement_changes(self) -> AgentResponse:
        # Assuming self.step["save_file"] is a list of files to process
        files_to_process = self.step["save_file"]
        
        # Process each file in parallel
        tasks = [self.process_file(file_info) for file_info in files_to_process]
        results = await asyncio.gather(*tasks)

        # Handle results as needed (e.g., update state, handle errors)
        # ...

        return AgentResponse.done(self)

    async def process_file(self, file_info):
        file_name = file_info["path"]
        # Implement the file processing logic for each file
        # Fetch current file content, apply changes, etc.
        # ...

    async def describe_files(self) -> AgentResponse:
        llm = self.get_llm(DESCRIBE_FILES_AGENT_NAME)
        to_describe = {
            file.path: file.content.content for file in self.current_state.files if not file.meta.get("description")
        }

        for file in self.next_state.files:
            content = to_describe.get(file.path)
            if content is None:
                continue

            if content == "":
                file.meta = {
                    **file.meta,
                    "description": "Empty file",
                    "references": [],
                }
                continue

            log.debug(f"Describing file {file.path}")
            convo = (
                AgentConvo(self)
                .template(
                    "describe_file",
                    path=file.path,
                    content=content,
                )
                .require_schema(FileDescription)
            )
            llm_response: FileDescription = await llm(convo, parser=JSONParser(spec=FileDescription))

            file.meta = {
                **file.meta,
                "description": llm_response.summary,
                "references": llm_response.references,
            }
        return AgentResponse.done(self)

