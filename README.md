![Ollama icon](https://raw.githubusercontent.com/Thinking-Dragon/ollama-juju-charm/main/icon.svg)
# Charmed Ollama
[![Charmhub Badge](https://charmhub.io/ollama/badge.svg)](https://charmhub.io/ollama)

[Ollama](https://github.com/ollama/ollama) enables easy deployment of large language models on your own infrastructure.

See the models available in the [Ollama library](https://ollama.com/library).

## Installation
[![Get it from the Charmhub](https://charmhub.io/static/images/badges/en/charmhub-black.svg)](https://charmhub.io/ollama)

### Deploying Ollama on your cloud using Juju
```bash
juju deploy ollama --channel=beta
```

### Installing a large language model to use
```bash
juju run ollama/0 pull model="llama3.1"
```
Note: the *pull* action may take a long time, you can add the `--wait` parameter (i.e. `--wait=5m`) to avoid getting a timeout error if your model is too large.

## Usage
### Generating text using the juju action
```bash
juju run ollama/0 generate model="llama3.1" prompt="Why is the sky blue?"
```
Note: the *generate* action may take a long time, you can add the `--wait` parameter (i.e. `--wait=5m`) to avoid getting a timeout error if your hardware is too slow.

### Generating text using the HTTP API
```bash
curl http://<unit-ip-address>:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt":"Why is the sky blue?"
}'
```

## Other resources

- See the [Juju SDK documentation](https://juju.is/docs/sdk) for more information about developing and improving charms.
- See the [Ollama API documentation](https://github.com/ollama/ollama/blob/main/docs/api.md) for all the interactions you can have with Ollama.
