"""
Script pour ajouter un prompt de test dans prompts_working.db
"""

import sqlite3

def add_test_prompt():
    conn = sqlite3.connect('g:/tmp/prompts_working.db')
    cursor = conn.cursor()
    
    # Ajouter un prompt de test
    cursor.execute('''INSERT INTO prompts 
                     (name, prompt_values, workflow, url, model, comment, status) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                  ('Test Prompt', '{}', '{}', '', 'test_model', 
                   'Prompt de test pour vérifier le rechargement', 'new'))
    
    conn.commit()
    
    # Vérifier
    cursor.execute('SELECT COUNT(*) FROM prompts')
    count = cursor.fetchone()[0]
    print(f'Total prompts dans prompts_working.db: {count}')
    
    cursor.execute('SELECT id, name, status FROM prompts')
    prompts = cursor.fetchall()
    print('Prompts:')
    for prompt in prompts:
        print(f'  {prompt[0]}: {prompt[1]} ({prompt[2]})')
    
    conn.close()

if __name__ == "__main__":
    add_test_prompt()