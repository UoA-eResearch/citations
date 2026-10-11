"""D3: BOS handling of Herald's tokenizer after the tokenizer_class fix (as the completions endpoint encodes)."""
from transformers import AutoTokenizer
t = AutoTokenizer.from_pretrained("/models/Herald_translator")
ids = t.encode("User:hello\n\nAssistant:", add_special_tokens=True)
print("first ids", ids[:3], "bos_id", t.bos_token_id, "bos", t.bos_token, "eos", t.eos_token, t.eos_token_id)
print(t.convert_ids_to_tokens(ids[:3]))
