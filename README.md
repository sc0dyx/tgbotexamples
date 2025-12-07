```bash
git clone https://github.com/sc0dyx/tgbotexamples
cd tgbotexamples
```

# artificial intelligence
```bash
cd AIbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
wget -O models/model-q8_0.gguf 'https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/resolve/main/model-q8_0.gguf?download=true'
python main.py
```
# currency bot
```bash
cd currencybot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
# rpg bot
```bash
cd rpgbot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

# links
- [HuggingFace: Saiga LLaMA3 8B GGUF models](https://huggingface.co/IlyaGusev/saiga_llama3_8b_gguf/tree/main)
- [Documentation HuggingFace](https://huggingface.co/docs)
- [Aiogram](https://docs.aiogram.dev/)
- [Python](https://www.python.org/)
