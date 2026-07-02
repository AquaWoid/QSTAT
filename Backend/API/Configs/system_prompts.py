codebook_structure = """
  [
    {
      "id": "tc1",
      "name": "Example Name",
      "color": "3",
      "count": 0,
      "open": true,
      "desc": "Example Description",
      "children": [
        {
          "id": "tc1c1",
          "name": "Example Name",
          "color": "3",
          "count": 0,
          "desc": "Example Description"
        }
      ]
    },
    {
      "id": "tc2",
      "name": "Example Name",
      "color": "5",
      "count": 0,
      "open": true,
      "desc": "Example Description",
      "children": [
        {
          "id": "tc2c1",
          "name": "Example Name",
          "color": "5",
          "count": 0,
          "desc": "Example Description"
        }
      ]
    },
    {
      "id": "tc3",
      "name": "Example Name",
      "color": "2",
      "count": 0,
      "open": true,
      "desc": "Example Description",
      "children": [
        {
          "id": "tc3c1",
          "name": "Example Name",
          "color": "3",
          "count": 0,
          "desc": "Example Description"
        }
      ]
    },
    {
      "id": "tc4",
      "name": "Example Name",
      "color": "3",
      "count": 0,
      "open": true,
      "desc": "Example Description",
      "children": [
        {
          "id": "tc4c1",
          "name": "Example Name",
          "color": "3",
          "count": 0,
          "desc": "Example Description"
        },
        {
          "id": "tc4c2",
          "name": "Example Name",
          "color": "3",
          "count": 0,
          "desc": "Example Description"
        }
      ]
    },
    {
      "id": "tc5",
      "name": "Example Name",
      "color": "4",
      "count": 0,
      "open": true,
      "desc": "Example Description",
      "children": [
        {
          "id": "tc5c1",
          "name": "Example Name",
          "color": "4",
          "count": 0,
          "desc": "Example Description"
        }
      ]
    },
    {
      "id": "tc6",
      "name": "Example Name",
      "color": "5",
      "count": 0,
      "open": true,
      "desc": "Example Description",
      "children": [
        {
          "id": "tc6c1",
          "name": "Example Name",
          "color": "5",
          "count": 0,
          "desc": "Example Description"
        }      
      ]
    },
    {
      "id": "tc7",
      "name": "Example Name",
      "color": "6",
      "count": 0,
      "open": true,
      "desc": "Example Description",
      "children": [
        {
          "id": "tc7c1",
          "name": "Example Name",
          "color": "6",
          "count": 0,
          "desc": "Example Description"
        }      
      ]
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

  Remember the names and descriptions in the schema are only examples, find matching names and descriptions from the source material provided by the user!

  
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



def get_deductive_codebook_prompt(min_codes : int, max_codes : int, docname: str):


  deductive_codebook_creation = f"""

  You are a system for creating code systems for qualitative research. 

  The way you the system must tightly follow Phillip Mayring's deduktive category application (deduktive Kategorienanwendung)

  Your task is to generate a valid JSON object representing a qualitative codebook based on the user input research question and document.

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
  Remember the names and descriptions in the schema are only examples, find matching names and descriptions from the source material provided by the user!
  IMPORTANT: in every id you have to use the document identifier {docname} before the actual id with an underline in the middle. Example: docname_id

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

