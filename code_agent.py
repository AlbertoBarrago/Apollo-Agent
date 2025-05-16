from google.generativeai.types import AuthorError
from transformers.agents import CodeAgent
from transformers import Tool, AutoTokenizer, AutoModelForCausalLM
from typing import Dict, Any, List

from agent import ApolloAgent

class HuggingFaceTools:
    """

    """
    def __init__(self, apollo_agent: ApolloAgent):
        """
        Inizializza HuggingFaceTools con un'istanza esistente di ApolloAgent.
        """
        self.apollo_agent = apollo_agent
        self.code_agent = None
        self._prepared_tools: List[dict] = []
        try:
            # Prova ad autenticarti automaticamente se hai usato huggingface-cli login
            self.tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", token=True)
            self.model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B-Instruct", token=True)
            print("Modello Llama 3.1-8B-Instruct caricato con autenticazione automatica.")
        except AuthorError as e:
            print(f"Errore durante il caricamento del modello con autenticazione automatica: {e}")
            print("Assicurati di aver richiesto l'accesso al modello e di essere loggato con 'huggingface-cli login'.")
            # Puoi scegliere di caricare un modello di fallback qui se necessario
            self.tokenizer = None
            self.model = None

    def _prepare_tools_for_code_agent(self) -> List[Tool]:
        """
        Prepara i metodi di ApolloAgent come una lista di oggetti Tool per il CodeAgent.
        """
        tools: List[Tool] = []
        for tool_spec in self.apollo_agent.get_available_tools():
            tool_name = tool_spec["name"]
            if hasattr(self.apollo_agent, tool_name):
                tool_function = getattr(self.apollo_agent, tool_name)
                tool = Tool(
                    name=tool_name,
                    func=tool_function,
                    description=tool_spec["description"],
                    parameters=tool_spec["parameters"],
                )
                tools.append(tool)
                self._prepared_tools.append(tool_spec) # Popola anche la lista di specifiche
        return tools

    def prepare_code_agent(self):
        """
        Prepara e inizializza il CodeAgent.
        """
        tools = self._prepare_tools_for_code_agent()
        self.code_agent = CodeAgent(
            tools=tools # Passa direttamente la lista di oggetti Tool
        )

    def get_tools(self) -> list[dict]:
        """
        Restituisce la lista delle specifiche degli strumenti preparati per l'integrazione.
        """
        return self._prepared_tools # Restituisce la lista di specifiche preparata

    async def run_code_agent(self, instruction: str):
        """
        Esegue l'Hugging Face CodeAgent con un'istruzione in linguaggio naturale.
        """
        if not self.code_agent:
            return {"error": "CodeAgent non ancora inizializzato."}
        try:
            result = await self.code_agent.run(instruction)
            return result
        except RuntimeError as e:
            return {"error": f"Esecuzione di CodeAgent fallita: {str(e)}"}

    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Esegue direttamente uno strumento gestito dal CodeAgent.
        """
        if not self.code_agent:
            return {"error": "CodeAgent non ancora inizializzato."}
        tool = next((t for t in self.code_agent.tools if t.name == tool_name), None)
        if not tool:
            return {"error": f"Strumento {tool_name} non trovato in CodeAgent"}
        try:
            result = await tool.func(**kwargs)
            return {"result": result}
        except RuntimeError as e:
            return {"error": str(e)}