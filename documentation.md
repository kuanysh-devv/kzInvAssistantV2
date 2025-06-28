 📡 WebSocket API Documentation — Assistant Chat

A real-time WebSocket API for users to chat with assistants.

---

## 🔗 WebSocket Endpoint

- **URL:** `ws://server-ip/ws/assistant`
- **Protocol:** JSON
- **Authorization:** ❌ Not required (public access)

---

## 📥 Client → Server Messages

### 🔍 `get_assistants`

Request a list of available assistants.

```json
{
  "type": "get_assistants"
}
```

### ✅ `select_assistant`

Select one of the assistants by ID. Must be called before sending questions.

```json
{
  "type": "select_assistant",
  "assistant_id": 1
}
```

### ❓ `question`
Ask a question to the selected assistant.

```json

{
  "type": "question",
  "question": "What is happening?"
}
```

## 📤 Server → Client Messages


### 📜 `assistant_list`
Returned in response to "get_assistants".

```json
{
  "type": "assistant_list",
  "assistants": [
    {
      "id": 1,
      "name": "Общий ассистент",
      "description": "Отвечает на общие вопросы"
    }
  ]
}
```
### ✅ `success`
A confirmation message from 'select_assistant'.

```json
{
  "type": "success",
  "message": "Ассистент выбран: Общий ассистент"
}
```

### ❌ `error`
Error message with a description of what went wrong.

```json
{
  "type": "error",
  "message": "Ассистент не найден"
}
```

### 💬 answer
Returned in response to "question".

```json
{
  "type": "answer",
  "message": "Answer example"
}
```

error will be returned in this format

```json
{
  "type": "error",
  "message": "Something went wrong..."
}

```


## 🛠 Example Flow

### 1. Connect to WebSocket: ws://server-ip/ws/assistant
### 2. Send:
```json
{ "type": "get_assistants" }
```
### 3. Then select assistant from list:
```json
{ "type": "select_assistant", "assistant_id": 1 }
```
### 4. Then ask a question:
```json
{ "type": "question", "question": "Any questions?" }
```
### 5. Receive the answer:
```json
{ "type": "answer", "message": "..." }
```

## * All interactions are stateless. If a client reconnects, they must select the assistant again.

## * When a user disconnects, the selected assistant is removed from cache.

## * The assistant will return a fallback message like "К сожалению, по вашему вопросу не найдено подходящей информации..." if no document-based answer is found.

