from langchain.llms import LlamaCpp
from langchain import PromptTemplate, LLMChain
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler 
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent


def process_llm(df):
    template = """
    You are an analyst who explains the vegetation index. 
    {question} has a relative ratio of four seasons.
    Please explain this to me.
    """

    prompt = PromptTemplate(template=template, input_variables=["question"])

    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])

    llm = LlamaCpp(
                    model_path="firefly-llama2-13b-chat.Q4_K_M.gguf",
                    input={"temperature": 0.75,
                        "max_length": 4000,
                        "top_p": 1},
                    callback_manager=callback_manager,
                    n_ctx=2048
                    )

    agent = create_pandas_dataframe_agent(llm, df, verbose=True)

    answer = agent.run(prompt)

    return answer 