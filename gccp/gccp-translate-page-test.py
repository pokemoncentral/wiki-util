import importlib

gccptranslatepage = importlib.import_module("gccp-translate-page")

# tests
if __name__ == "__main__":
    text = "Grass Metal Metallic {{TCGPocketPokémonPrevNext}}"
    assert (
        gccptranslatepage.replacements_from_file(text, "gccp-replacements.csv")
        == "Erba Metallo Metallic {{GCCPocketPokémonPrevNext}}"
    )
