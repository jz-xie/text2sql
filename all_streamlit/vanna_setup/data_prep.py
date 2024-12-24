import json
from navigation import APP_DIR


def generate_ddl(db_name: str ="superhero") -> list[str]:
   with open(f'{APP_DIR}/../sample_data/dev_tables.json', 'r') as file:
      data = json.load(file)
      
   db_data = [i for i in data if i["db_id"]==db_name][0]
   ddl_statements = []
   
   table_names = db_data['table_names_original']
   column_names = db_data['column_names_original']
   column_types = db_data['column_types']
   
   for table_index in range(len(table_names)):
      table_name = table_names[table_index]
      
      ddl = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
      
      columns = []
      
      for col_index in range(len(column_names)):
         if column_names[col_index][0] == table_index:  # Match column to the correct table
               col_name = column_names[col_index][1]
               col_type = column_types[col_index]  # Default to TEXT if type not found
               
               # Define primary key for id columns
               if col_name == "id":
                  column_definition = f"    {col_name} {col_type} PRIMARY KEY"
               else:
                  column_definition = f"    {col_name} {col_type}"
               
               columns.append(column_definition)
      
      ddl += ",\n".join(columns) + "\n);\n"
      
      ddl_statements.append(ddl)
   
   return ddl_statements


def generate_question_sql(db_name:str="superhero") -> list[str]:
   with open(f'{APP_DIR}/../sample_data/dev.json', 'r') as file:
      data = json.load(file)
      
   db_data = [i for i in data if i["db_id"]==db_name]
   question_sql_pairs = []
   for raw_pair in db_data:
      pair = {
         "question": raw_pair["question"],
         "sql": raw_pair["SQL"]
      }
      question_sql_pairs.append(pair)
   
   return question_sql_pairs