# Cakto Split Engine

API de pagamentos construída em **Django + Django REST Framework**, com foco em **precisão financeira**, **idempotência** e **boas práticas de domínio**.

---

## Stack utilizada

- **Python: 3.12.3**
- **Django: 6.0.2**
- **Django REST Framework: 3.16.1**
- **SQLite**
- **Pytest**
- **virtualenv: 20.26.2**

---

## Estrutura do projeto

```
cakto-split-engine/
├── app/
│   ├── api/            # Views, URLs, Serializers
│   ├── models/         # Models (Payment, LedgerEntry, OutboxEvent)
│   ├── services/       # Regras de negócio
│   └── tests.py        # Testes automatizados
├── config/
│   ├── settings.py
│   └── urls.py
├── manage.py
├── requirements.txt
└── README.md
```

---

## Endpoints

### `POST /api/v1/payments`

Confirma o pagamento com suporte a **idempotência**.

**Headers**

```
Idempotency-Key: <id>
```

**Request (exemplo):**

```json
{
  "amount": "100.00",
  "currency": "BRL",
  "payment_method": "card",
  "installments": 1,
  "splits": [
    { "recipient_id": "producer_1", "role": "producer", "percent": 90 },
    { "recipient_id": "affiliate_1", "role": "affiliate", "percent": 10 }
  ]
}
```

**Response (exemplo):**

```json
{
  "payment_id": "id",
  "status": "CAPTURED",
  "gross_amount": "100.00",
  "platform_fee_amount": "10.00",
  "net_amount": "90.00",
  "receivables": [
    { "recipient_id": "producer_1", "role": "producer", "amount": "81.00" },
    { "recipient_id": "affiliate_1", "role": "affiliate", "amount": "9.00" }
  ],
  "outbox_event": {
    "type": "payment_captured",
    "status": "PENDING"
  }
}
```

---

### `POST /api/v1/checkout/quote`

Gera uma simulação de valores (gross, fees, net).

**Request (exemplo):**

```json
{
  "amount": "100.00",
  "currency": "BRL",
  "payment_method": "card",
  "installments": 1,
  "splits": [
    { "recipient_id": "producer_1", "role": "producer", "percent": 100 }
  ]
}
```

---

## Como rodar o projeto localmente

### 1. Criar o virtualenv

```sh
$ python -m virtualenv venv
$ source venv/bin/activate
```

### 2. Instalar dependências

```sh
$ pip install -r requirements.txt
```

### 3. Rodar migrations

```sh
$ python manage.py makemigrations
$ python manage.py migrate
```

### 4. Subir o servidor

```sh
$ python manage.py runserver
```

A API ficará disponível em: `http://localhost:8000`

---

## Rodando os testes

```sh
$ python -m pytest
```

Os testes usam banco de dados isolado criado automaticamente pelo `pytest-django`.

---

## Decisões técnicas

### 1. Precisão e arredondamento

Para garantir precisão em todos os cálculos financeiros, o sistema **não utiliza floats em nenhum ponto**.  
Todos os valores monetários são representados usando `Decimal`, evitando erros de ponto flutuante típicos de `float`.

- **Entrada de valores**

  - O DRF `DecimalField` é usado nos serializers.
  - O service assume que os valores já chegam como `Decimal`, garantindo tipagem correta na camada de regras de négocio.

- **Cálculo de taxa da plataforma**

  - Utiliza `ROUND_HALF_UP`, que é o padrão mais comum em sistemas financeiros.

---

### 2. Regra dos centavos (rounding strategy)

Ao dividir o valor líquido (`net_amount`) entre múltiplos recebedores, é inevitável que ocorram sobras de centavos devido ao arredondamento para duas casas decimais.

#### Regra adotada

1. Cada split é calculado individualmente
2. O valor é **arredondado para baixo (`ROUND_DOWN`)**
3. Após distribuir todos os splits, calcula-se o `remainder`.
4. O centavo (ou centavos) restante é atribuído **ao recebedor com o maior percentual de split**.

Caso haja empate de percentuais, o primeiro recebedor da lista (ordem de entrada) é utilizado como critério de desempate, garantindo determinismo.

---

### 3. Estratégia de idempotência

- Cada request usa um `Idempotency-Key`
- O payload é hashado e armazenado junto ao pagamento
- Requisições repetidas:

  - Retornam o mesmo resultado se o payload for igual
  - Geram erro se o payload for diferente

Isso evita:

- Pagamentos duplicados
- Efeitos colaterais em retries

---

### 4. Métricas para produção

- Total de pagamentos por status
- Latência do `confirm_payment`
- Conflitos de idempotência
- Diferença entre gross e net (fees agregadas)

---

### 5. Próximos passos (se houvesse mais tempo)

- Observabilidade (logs estruturados + tracing)
- Testes end-to-end
- Suporte a múltiplas moedas

---

## Uso de IA

- Foi utilizado GitHub Copilot para acelerar a escrita de código e testes.
- Foi utilizado ChatGPT para escrita da documentação.

---

## Pull Requests

- [Setup: Initialize Django Project #1](https://github.com/th92rodr/cakto-split-engine/pull/1)
- [Feature: Define Database Schema #2](https://github.com/th92rodr/cakto-split-engine/pull/2)
- [Feature: Fee and Split Calculation #3](https://github.com/th92rodr/cakto-split-engine/pull/3)
- [Feature: API Endpoints #4](https://github.com/th92rodr/cakto-split-engine/pull/4)

---

## License

Este projeto está licenciado sob a [MIT License](LICENSE.md).

---

## Author

[**@th92rodr**](https://github.com/th92rodr)
