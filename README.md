# textAnalyzer

TextAnalyzer is a project that streamlines routine text analysis tasks by using Large Language Models (LLMs) with specific prompts to quickly filter and extract desired information from various documents, saving time and effort in the content processing.

### Deployment

1. Setup the [python 3.11.3 env](https://www.python.org/downloads/) and install
    * Suggest using virtual env
```shell
pip install -r requirement.txt
```

2. Download the repository
```shell
git clone https://github.com/reid41/textAnalyzer.git
cd textAnalyzer
```

3. Specify the LLM API in `config/config.ini` or set it after startup

4. Startup
```shell
python llm_main.py
```

5. Define the prompt and input the text to analyze

