In this tutorial, you will deploy the *Ollama* charm and build a simple chat-bot that uses *Ollama* to answer the user's messages.

# Deploying Ollama
First, you need to deploy *Ollama* using the Juju Charm:
```bash
juju deploy ollama --channel beta
```

Wait until the *Ollama* charm is installed and running.

Once running, the charm will expose an HTTP server with the same format as OpenAI's API. You can find all the endpoints available in the [Ollama repository](https://github.com/ollama/ollama/blob/main/docs/api.md).

# Pulling a model to use
Before you can use a large language model, you need to pull the model you want. This will download the model from a remote repository to your local *Ollama* instance.
```bash
juju run ollama/0 pull model="mistral" --wait=5m
```

The `--wait=5m` parameter extends the timeout to five minutes because pulling a model will typically take some time (depending on your Internet connection).

In this example, we are pulling `mistral` (only 7 billion parameters). This model will run on most hardware. This is why we are using it for the tutorial. If you have a more powerful machine, you can replace `mistral` with another available model of your choice and continue with this tutorial without any issue.

You can find a list of all available models in the [Ollama models library](https://ollama.com/library).

# Generating text using the model
Now that you have pulled a model, you can use it to generate text.
```bash
juju run ollama/0 generate model="mistral" prompt="Why is the sky blue?"
```

Response:
```
Running operation 98 with 1 task
  - task 99 on unit-ollama-26

Waiting for task 99...
18:15:20 Executing prompt…

model: mistral
response: 'The sky appears blue because of a process called Rayleigh scattering.
  In simple terms, when sunlight reaches Earth''s atmosphere, it is made up of different colors, each with slightly different wavelengths. Shorter wavelengths (like violet and blue) are scattered in all directions more than longer wavelengths (like red, yellow, and green).
  However, our eyes are more sensitive to blue light, and we perceive the sky as blue rather than violet. Additionally, sunlight reaches us more from the blue part of the spectrum because violet light is scattered even more strongly than blue, but it's absorbed by the ozone layer before reaching our eyes.'
timestamp: "2024-08-05T18:15:57.275580855Z"
```

Note that you can add `--wait=5m` (choose the appropriate timeout for your hardware setup) if your computer is likely to take a long time to run the inference. Typically, this will be useful if you do not have a GPU and you are running *Ollama* on your CPU.

# Writing a simple chat-bot
Finally, let's create a simple application that uses *Ollama* to answer the user's messages.

## Creating the chat-bot

Create a new Python file `chat-bot.py`.
```python
#!/usr/bin/env python3

from os import getlogin
from sys import argv

from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

def main():
	username = getlogin()

	ollama_url = argv[1]
	model = argv[2]

	llm = ChatOllama(
		base_url = ollama_url,
		model = model,
	)

	message_history = [
	SystemMessage(content = f"""
		You are a friendly assistant.
		Your job is to answer the user's messages.
		The user is called {username}.
		You will reply with concise yet friendly responses.
		You prefer short answers over long ones.
		If you do not know an answer, you will say that you don't know.
		Never invent something you don't know.
	""")
	]

	while True:
		user_message = input(format_user_message(username))
		message_history.append(HumanMessage(content = user_message))

		ai_message = llm.invoke(message_history).content
		message_history.append(AIMessage(content = ai_message))

		print(format_ai_message(model, ai_message))

def format_user_message(username: str) -> str:
	"""
		Formats the user prompt like follows:
			┌── <Username>
			└─ [User types their message here]
	"""
	return f"┌── {username}\n└─ "

def format_ai_message(model_name: str, message: str) -> str:
	"""
		Formats the AI's response like follows:
			┌── <Model name>
			│
			│ <The AI's response>
			│
			└─
	"""
	indented_message = "│ " + message.replace("\n", "\n│ ")
	return f"\n┌── {model_name}\n│\n{indented_message}\n│\n└─\n"

if __name__ == "__main__":
	main()
```

Here are the dependencies for this program `requirements.txt`.
```txt
langchain==0.1.6
langchain-community==0.0.19
```

To interact with a large language model through *Ollama* you can, as mentioned above, make HTTP requests to the [endpoints](https://github.com/ollama/ollama/blob/main/docs/api.md) exposed by the *Ollama* server.

Conveniently, [LangChain](https://langchain.com/) has an [Ollama integration](https://python.langchain.com/v0.2/docs/integrations/providers/ollama/) which makes it trivial to switch your existing LangChain application to *Ollama*.

In this tutorial, we are using the *Ollama* integration to send messages to the [/api/chat](https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion) endpoint (by invoking the `ChatOllama` class).

## Running your chat-bot using Ollama

First, you need to know your *Ollama* instance's IP address and port. You can run `juju status` to find it.

```bash
$ juju status

Model          Controller           Cloud/Region         Version  SLA          Timestamp
machine-cloud  localhost-localhost  localhost/localhost  3.5.3    unsupported  21:19:54Z

App     Version  Status  Scale  Charm   Channel  Rev  Exposed  Message
ollama           active      1  ollama            23  no       Ollama is running

Unit        Workload  Agent  Machine  Public address  Ports      Message
ollama/26*  active    idle   26       10.88.109.53    11434/tcp  Ollama is running

Machine   State    Address       Inst id               Base          AZ  Message
26        started  10.88.109.53  juju-1f1bae-26        ubuntu@22.04      Running
```

In this example, the values you are looking for are:
- *Ollama IP address*: `10.88.109.53`
- *Ollama port*: `11434`

### Run your chat-bot
```bash
$ ./chat-bot.py http://<ollama_ip>:<ollama_port> mistral
```
If you are using another model (not `mistral`), then replace `mistral` with the name of the model you have pulled from the library.

### You can now have a conversation
```txt
┌── thinking-dragon
└─ Hi!

┌── mistral
│
│ Hello there, thinking-dragon! How can I help you today?
│
└─

┌── thinking-dragon
└─ Why is the sky blue?

┌── mistral
│
│ The sky appears blue due to a phenomenon called Rayleigh scattering.
│ Shorter wavelengths of light (like blue) are scattered more easily by
│ the molecules in Earth's atmosphere compared to longer wavelengths (like red).
│ This scattering of blue light gives our sky its characteristic color.
│
└─

┌── thinking-dragon
└─ You are a geography expert. Your job is, for a given place name, to give the WGS84 coordinates of that place. Your response will be in json format. Your json response will contain two keys: 'lat' for the latitude and 'lon' for the longitude. You will reply with the json response only and nothing else. You will not add any personal remark. Give the coordinates for 'Montreal'.

┌── mistral
│
│ {"lat": 45.508391, "lon": -73.587666}
│
└─
```

For reference, you can type `45.508391, -73.587666` in Google Maps and you will see that the coordinates are indeed in the middle of the Montreal island. This is however an estimation. While LLMs will give you varying precision for this use-case, they will all estimate and not be consistent if you run the same prompt multiple times.
