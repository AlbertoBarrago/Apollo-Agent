from transformers.agents import CodeAgent
from transformers import Tool, AutoTokenizer, AutoModelForCausalLM
from typing import Dict, Any, List

from agent import ApolloAgent


class HuggingFaceTools:
    """
     HuggingFaceTools Code Agent
    """

    def __init__(self, apollo_agent: ApolloAgent):
        """
        Inizializza HuggingFaceTools con un'istanza esistente di ApolloAgent.
        """
        self.apollo_agent = apollo_agent
        self.code_agent = None
        self._prepared_tools: List[dict] = []
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                "meta-llama/Llama-3.1-8B-Instruct"
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                "meta-llama/Llama-3.1-8B-Instruct"
            )
            print(
                "Modello Llama 3.1-8B-Instruct caricato con autenticazione automatica."
            )
        except RuntimeError as e:
            print(
                f"Errore durante il caricamento del modello con autenticazione automatica: {e}"
            )
            print(
                "Assicurati di aver richiesto l'accesso al modello e di essere loggato con 'huggingface-cli login'."
            )

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
                tool = Tool()
                tool.name = tool_name
                tool.func = tool_function
                tool.description = tool_spec["description"]

                tool.inputs = {
                    param["name"]: {"type": param["type"], "description": param["description"]}
                    for param in tool_spec["parameters"]
                }
                tool.output_type = "string"

                tools.append(tool)
                self._prepared_tools.append(tool_spec)
        return tools

    def prepare_code_agent(self):
        """
        Prepara e inizializza il CodeAgent.
        """
        tools = self._prepare_tools_for_code_agent()
        self.code_agent = CodeAgent(tools=tools)

    def get_tools(self) -> list[dict]:
        """
        Restituisce la lista delle specifiche degli strumenti preparati per l'integrazione.
        """
        return self._prepared_tools  # Restituisce la lista di specifiche preparata

    async def run_code_agent(self, instruction: str):
        """
        Esegue l'inferenza del modello Llama direttamente con l'istruzione fornita.
        """
        if not self.model or not self.tokenizer:
            return {"error": "Modello Llama o tokenizer non caricati correttamente."}
        try:
            inputs = self.tokenizer(instruction, return_tensors="pt").to(
                self.model.device)  # Move inputs to the model's device

            generate_ids = self.model.generate(inputs.input_ids, max_length=200, num_beams=5, no_repeat_ngram_size=2,
                                               early_stopping=True)

            outputs = self.tokenizer.batch_decode(generate_ids, skip_special_tokens=True,
                                                  clean_up_tokenization_spaces=False)
            return {"result": outputs[0]}
        except RuntimeError as e:
            return {"error": f"Errore durante l'esecuzione dell'inferenza locale: {str(e)}"}

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
