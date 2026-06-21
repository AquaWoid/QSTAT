codebook_structure = """
  [
    {
      "id": "tc1",
      "name": "Data Cleaning Challenges",
      "color": "3",
      "count": 0,
      "open": true,
      "desc": "Discussion around difficulties in cleaning and categorizing data, including ambiguity in tagging entities like people, places, and organizations.",
      "children": [
        {
          "id": "tc1c1",
          "name": "JSON",
          "color": "3",
          "count": 0,
          "desc": ""
        }
      ]
    },
    {
      "id": "tc2",
      "name": "Tool Development Purpose",
      "color": "5",
      "count": 0,
      "open": true,
      "desc": "Focus on creating a data processing tool to assist with data accessibility and usability for academic projects.",
      "children": [
        {
          "id": "tc2c1",
          "name": "TestCode",
          "color": "5",
          "count": 0,
          "desc": ""
        }
      ]
    },
    {
      "id": "tc3",
      "name": "Collaborative Efforts",
      "color": "2",
      "count": 0,
      "open": true,
      "desc": "Mentions of teamwork, disagreements, and collaborative processes in handling and organizing data.",
      "children": []
    },
    {
      "id": "tc4",
      "name": "Domain Knowledge Requirements",
      "color": "3",
      "count": 0,
      "open": true,
      "desc": "How participants describe needed subject-matter knowledge (e.g., historical context, taxonomies) to interpret and structure the data correctly.",
      "children": [
        {
          "id": "tc4c1",
          "name": "Test Code",
          "color": "3",
          "count": 0,
          "desc": ""
        },
        {
          "id": "tc4c2",
          "name": "Testcode2",
          "color": "3",
          "count": 0,
          "desc": ""
        }
      ]
    },
    {
      "id": "tc5",
      "name": "Data Quality and Validation Criteria",
      "color": "4",
      "count": 0,
      "open": true,
      "desc": "Processes and standards used to judge whether cleaned/tagged data are correct, consistent, and trustworthy.",
      "children": [
        {
          "id": "tc5c1",
          "name": "data",
          "color": "4",
          "count": 0,
          "desc": ""
        }
      ]
    },
    {
      "id": "tc6",
      "name": "Uncertainty, Ambiguity, and Edge Cases",
      "color": "5",
      "count": 0,
      "open": true,
      "desc": "Examples of ambiguous entries and difficulties in disambiguating entity types (person/place/group/org) or handling atypical records.",
      "children": []
    },
    {
      "id": "tc7",
      "name": "User Workflows and Adoption Barriers",
      "color": "6",
      "count": 0,
      "open": true,
      "desc": "Insights into how end users would use the tool, including friction points, expectations, and obstacles to adoption in research workflows.",
      "children": []
    }
  ]

"""



def get_codebook_prompt(min_codes : int, max_codes : int):


  codebook_creation = f"""

  You are a structured data extraction system.

  Your task is to generate a valid JSON object representing a qualitative codebook based on an input text (e.g. interview transcript or other content).

  You MUST follow these rules strictly:

  1. Output ONLY valid JSON. No explanations, no comments, no extra text before or after.
  2. The JSON must be syntactically correct and parsable.
  3. Use double quotes for all keys and string values.
  4. Do not include trailing commas.
  5. Do not include undefined or null fields. Always fill fields with meaningful content.
  6. Keep all text in the same language as the input.

  ### JSON Structure

  The output must follow exactly this schema:

  {codebook_structure}


  ### Coding Guidelines

  - Identify meaningful themes, concepts, or categories in the text.
  - Create clear, concise, and descriptive code names.
  - Group related codes under a parent code using "subcodes".
  - Only create "subcodes" if there is a clear hierarchical relationship.
  - Avoid duplication.
  - Keep definitions precise and analytical, not vague.
  - Use short excerpts from the text as examples.
  - "notes" can include context, ambiguity, or coding guidance.
  - Use sequental and unique IDs following the provided schema.

  ### Output Constraints

  - Minimum {min_codes} codes.
  - Maximum {max_codes} codes.
  - Each code should have at least 1 meaningful sentence in "definition".
  - Use subcodes where appropriate, but do not force them.

  Remember:
  Output ONLY the valid JSON object. Nothing else.
  If the output is not in the input language translate it.
  """

  return codebook_creation



def get_deductive_codebook_prompt(min_codes : int, max_codes : int):


  deductive_codebook_creation = f"""

  You are a system for creating code systems for qualitative research. 

  The way you the system must tightly follow Phillip Mayring's deduktive category application (deduktive Kategorienanwendung)

  Your task is to generate a valid JSON object representing a qualitative codebook based on an user input research question and 10 relevant papers to that question.

  You MUST follow these rules strictly:

  1. Output ONLY valid JSON. No explanations, no comments, no extra text before or after.
  2. The JSON must be syntactically correct and parsable.
  3. Use double quotes for all keys and string values.
  4. Do not include trailing commas.
  5. Do not include undefined or null fields. Always fill fields with meaningful content.
  6. Keep all text in the same language as the input.

  ### JSON Structure

  The output must follow exactly this schema:

  {codebook_structure}


  ### Coding Guidelines

  - Identify meaningful themes, concepts, or categories in the source material.
  - Create clear, concise, and descriptive code names.
  - Group related codes under a parent code using "subcodes".
  - Only create "subcodes" if there is a clear hierarchical relationship.
  - Avoid duplication.
  - Keep definitions precise and analytical, not vague.
  - Use short excerpts from the text as examples.
  - Always cite correctly if you have used a paper for a category, the citation belongs in the description.
  - "notes" can include context, ambiguity, or coding guidance.
  - Use sequental and unique IDs following the provided schema.

  ### Output Constraints

  - Minimum {min_codes} codes.
  - Maximum {max_codes} codes.
  - Each code should have at least 1 meaningful sentence in "definition".
  - Use subcodes where appropriate, but do not force them.

  Remember:
  Output ONLY the valid JSON object. Nothing else.
  If the output is not in the input language translate it.
  """

  return deductive_codebook_creation

