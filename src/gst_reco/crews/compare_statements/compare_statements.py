from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Optional
from pydantic import BaseModel, Field


class SingleOutput(BaseModel):
    matched: bool
    id: Optional[int] = None


class BatchOutput(BaseModel):
    matches: List[SingleOutput] = Field(default_factory=list)


@CrewBase
class CompareStatements():
    """Crew that compares bank and book statement descriptions"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def matcher(self) -> Agent:
        return Agent(
            config=self.agents_config['matcher'],  # This must point to a defined agent in your YAML
            verbose=True
        )

    @task
    def batch_match_task(self) -> Task:
        return Task(
            config=self.tasks_config['batch_match_task'],  # Make sure this is defined in your YAML
            output_pydantic=BatchOutput,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.matcher()],
            tasks=[self.batch_match_task()],
            process=Process.sequential,
            verbose=True
        )
