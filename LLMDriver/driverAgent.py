"""
driver agent 可以通过调用工具来认知驾驶环境，进而做出驾驶决策。
Driver agents can perceive the driving environment by calling tools and make driving decisions accordingly.
"""

from rich import print
import sqlite3

from typing import Union
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI
from langchain.llms import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory, ConversationTokenBufferMemory
from langchain.callbacks import get_openai_callback
from langchain.agents.tools import Tool

from LLMDriver.callbackHandler import CustomHandler
from scenario.scenario import Scenario
from LLMDriver.agent_propmts import SYSTEM_MESSAGE_PREFIX, SYSTEM_MESSAGE_SUFFIX, FORMAT_INSTRUCTIONS, HUMAN_MESSAGE, TRAFFIC_RULES, DECISION_CAUTIONS


class DriverAgent:
    def __init__(
        self, llm: Union[ChatOpenAI, AzureChatOpenAI, OpenAI], toolModels: list, sce: Scenario,
        verbose: bool = False
    ) -> None:
        self.sce = sce
        self.ch = CustomHandler()
        self.llm = llm

        self.tools = []
        for ins in toolModels:
            func = getattr(ins, 'inference')
            self.tools.append(
                Tool(name=func.name, description=func.description, func=func)
            )

        # self.memory = ConversationBufferMemory(
        #     memory_key="chat_history", output_key='output'
        # )
        self.memory = ConversationTokenBufferMemory(
            memory_key="chat_history", llm=self.llm, max_token_limit=2048)

        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=verbose,
            memory=self.memory,
            agent_kwargs={
                'system_message_prefix': SYSTEM_MESSAGE_PREFIX,
                'syetem_message_suffix': SYSTEM_MESSAGE_SUFFIX,
                'human_message': HUMAN_MESSAGE,
                'format_instructions': FORMAT_INSTRUCTIONS,
            },
            handle_parsing_errors="Check your output and make sure it conforms the format instructions!",
            max_iterations=12,
            early_stopping_method="generate",
        )

    def agentRun(self, last_step_decision: dict):
        print(f'Decision at frame {self.sce.frame} is running ...')
        print('[green]Driver agent is running ...[/green]')
        self.ch.memory = []
        if last_step_decision is not None and "action_name" in last_step_decision:
            last_step_action = last_step_decision["action_name"]
            last_step_explanation = last_step_decision["explanation"]
        else:
            last_step_action = "Not available"
            last_step_explanation = "Not available"
        with get_openai_callback() as cb:
            self.agent.run(
                f"""
                You, the 'ego' car, are now driving a car on a highway. You have already drive for {self.sce.frame} seconds.
                The decision you made LAST time step was `{last_step_action}`. Your explanation was `{last_step_explanation}`. 
                Here is the current scenario: \n ```json\n{self.sce.export2json()}\n```\n. 
                Please make decision for the `ego` car. You have to describe the state of the `ego`, then analyze the possible actions, and finally output your decision. 

                There are several rules you need to follow when you drive on a highway:
                {TRAFFIC_RULES}

                Here are your attentions points:
                {DECISION_CAUTIONS}
                
                Let's think step by step. Once you made a final decision, output it in the following format: \n
                ```
                Final Answer: 
                    "decision":{{"ego car's decision, ONE of the available actions"}},
                    "expalanations":{{"your explaination about your decision, described your suggestions to the driver"}}
                ``` \n
                """,
                callbacks=[self.ch]
            )
        print(cb)
        print('[cyan]Final decision:[/cyan]')
        print(self.ch.memory[-1])
        self.dataCommit()

    def exportThoughts(self):
        output = {}
        output['thoughts'], output['answer'] = self.ch.memory[-1].split(
            'Final Answer:')
        return output

    def dataCommit(self):
        scenario = self.sce.export2json()
        thinkAndThoughts = '\n'.join(self.ch.memory[:-1])
        finalAnswer = self.ch.memory[-1]
        conn = sqlite3.connect(self.sce.database)
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO decisionINFO VALUES (?,?,?,?,?)""",
            (self.sce.frame, scenario, thinkAndThoughts, finalAnswer, '')
        )
        conn.commit()
        conn.close()
