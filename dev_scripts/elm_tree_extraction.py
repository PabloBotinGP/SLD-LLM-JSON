"""ELM/Decision tree-based extraction (renamed from 20_extract_elm_tree_final.py).
"""

import os
import networkx as nx
from openai import OpenAI
from elm.base import ApiBase
from elm.tree import DecisionTree
from sklearn import tree
from dotenv import load_dotenv

# Load API key from environment variable
load_dotenv()

client = OpenAI()

# Upload image using OpenAI Files API
def upload_image(file_path):
    with open(file_path, "rb") as f:
        result = client.files.create(file=f, purpose="user_data")
        return result.id

def Equipment_Inverter(file_id, **kwargs):
    G = nx.DiGraph(**kwargs)
    #G.graph["api"] = ApiBase(model="gpt-4o")
    G.graph["api"] = ApiBase(model="gpt-4.1-mini")

    formatting_instructions = (
        "\n\nProvide only the selected option as your first sentence."
        "\n\nThen, in a short paragraph, explain how you determined your answer based on the diagram or text."
        "\nCite specific language, components, or design elements that support your choice."
        "\nOnly choose one manufacturer exactly as it appears in the optionslist, in case there is a list."
        "\nIf there is no list, provide your own answer, but always the short answer first and then the explanation on a separate paragraph"
    )

    ApiBase.MODEL_ROLE = "You are an expert on analyzing Single Line Diagrams (SLD) of residential solar installations."

    # Lists
    manufacturer_list_json = [
        "Enphase Energy Inc.",
        "ABB",
        "SMA America",
        "SolarEdge Technologies",
        "Fronius USA",
        "OutBack Power",
        "Huawei",
        "Delta Electronics",
        "Chilicon Power",
        "other"
    ]

    G.add_node("intro_inverter_type",
        prompt=(
            f"I have provided you with a diagram (file ID: {file_id}). I want you to professionally analyze it and answer the following questions."
            "Use only clear evidence from the diagram and do not make assumptions."
            "Store your answers internally and provide them as a single JSON file at the end of the decision tree."
            "What is the architecture type used for all inverters in this project?"
            "Choose only one of the following options based on the ordinance text:"
            "- String Inverter without DC-DC Converters"
            "- String Inverter with DC-DC Converters"
            "- Microinverters"
            "- AC Modules"
            + formatting_instructions
        )
    )
    G.add_node("micro_mfr1", prompt=(
        "Inverter 1 Manufacturer.\n"
        "Choose from the following list:\n\n"
        + '\n'.join(f"- {m}" for m in manufacturer_list_json)
        + formatting_instructions
    ))
    G.add_node("micro_model1", prompt=(
        "Inverter 1 Model Number.\nPlease state the full model number as listed on the diagram or specification."
        + formatting_instructions
    ))
    G.add_node("micro_ocpd1", prompt=(
        "What is the maximum overcurrent protection device (OCPD) rating allowed on Inverter 1 (Amps)?"
        + formatting_instructions
    ))
    G.add_node("micro_interconnect1", prompt=(
        "Where will Inverter 1 be interconnected to the premises wiring and utility power?\n"
        "Select one of the following options:\n"
        "- Main Service Panel\n"
        "- Service Feeders\n"
        "- Backup Loads Panel"
        + formatting_instructions
    ))
    G.add_node("final", prompt=(
        "Here are the answers collected so far:\n"
        "{answers}\n\n"
        "Reformat them as a single JSON object."
        + formatting_instructions
    ))

    G.add_edge("intro_inverter_type", "micro_mfr1", condition=lambda x: x.strip().lower().startswith("microinverters"))
    G.add_edge("micro_mfr1", "micro_model1")
    G.add_edge("micro_model1", "micro_ocpd1")
    G.add_edge("micro_ocpd1", "micro_interconnect1")
    G.add_edge("micro_interconnect1", "final")

    return G

def main():
    #image_path = "SA20250410-5395-123-336.png"
    image_path = "test.jpg"
    file_id = upload_image(image_path)


    G = Equipment_Inverter(file_id)
    tree = DecisionTree(G)
    
    results = {}
    result= tree.run("intro_inverter_type")
    results["inverter_type"] = results

    if result.strip().lower().startswith("microinverters"):
        results["micro_mfr1"] = tree.run("micro_mfr1")
        results["micro_model1"] = tree.run("micro_model1")
        results["micro_ocpd1"] = tree.run("micro_ocpd1")
        results["micro_interconnect1"] = tree.run("micro_interconnect1")

        tree.run("final", context={"answers": results})

    print(tree.all_messages_txt)

if __name__ == "__main__":
    main()
