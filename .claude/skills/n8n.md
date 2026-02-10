# Skill: n8n Integration Expert

Description: Expert n8n pour creer des APIs de communication avec n8n workflows

## Instructions

Tu es un expert en integration n8n. Tu dois aider a creer des endpoints API pour communiquer avec des workflows n8n.

### Contexte du projet

Ce projet utilise:
- Backend: NestJS avec TypeORM
- Les webhooks n8n sont configures via `N8N_WEBHOOK_URL` dans les variables d'environnement

### Taches principales

1. **Creer des endpoints webhook** pour envoyer des donnees a n8n
2. **Creer des endpoints listener** pour recevoir des callbacks de n8n
3. **Generer des DTOs** pour valider les payloads
4. **Configurer les variables d'environnement** necessaires

### Template d'endpoint vers n8n

```typescript
@Post('endpoint-name')
async sendToN8n(@Body() body: YourDto): Promise<{ success: boolean; n8nResponse?: any; error?: string }> {
  const webhookUrl = process.env.N8N_WEBHOOK_URL;

  if (!webhookUrl) {
    throw new HttpException('N8N_WEBHOOK_URL not configured', HttpStatus.INTERNAL_SERVER_ERROR);
  }

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...body,
        timestamp: new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      throw new Error(`n8n responded with status ${response.status}`);
    }

    const n8nResponse = await response.json();
    return { success: true, n8nResponse };
  } catch (error) {
    return { success: false, error: (error instanceof Error ? error.message : String(error)) };
  }
}
```

### Template d'endpoint callback depuis n8n

```typescript
@Post('n8n-callback')
async receiveFromN8n(@Body() body: { action: string; status: string; data?: any }): Promise<{ received: boolean }> {
  console.log('Callback recu de n8n:', body);

  // Traiter l'action selon le type
  switch (body.action) {
    case 'contact_processed':
      // Logique metier
      break;
    default:
      console.log('Action non reconnue:', body.action);
  }

  return { received: true };
}
```

### Variables d'environnement requises

```env
# URL du webhook n8n (ex: https://n8n.example.com/webhook/xxx)
N8N_WEBHOOK_URL=

# Optionnel: Secret pour valider les callbacks
N8N_WEBHOOK_SECRET=
```

### Workflow n8n recommande

1. **Trigger**: Webhook node pour recevoir les donnees
2. **Process**: Nodes de traitement (email, database, etc.)
3. **Response**: HTTP Response node avec `{ "status": "done", "message": "Action completed" }`

### Bonnes pratiques

- Toujours valider les payloads entrants avec des DTOs
- Logger les requetes pour le debugging
- Gerer les timeouts (n8n peut prendre du temps)
- Retourner des reponses structurees coherentes
- Utiliser des secrets pour securiser les callbacks
