# Documentação

## 1. Contexto do projeto

Este projeto simula um **núcleo de pagamentos** de uma fintech.  
Essa fintech trabalha com **pagamentos de infoprodutos**, ou seja:

- Cursos online
- Mentorias
- E-books
- Conteúdos digitais vendidos por produtores

Em uma venda desse tipo, **o dinheiro raramente vai para uma única pessoa**.  
Normalmente:

- Parte fica com a **plataforma**
- Parte vai para o **produtor**
- Parte pode ir para **afiliados** ou outros participantes

Esse desafio foca exatamente nesse momento crítico:  
**quando um pagamento é confirmado e o dinheiro precisa ser calculado, dividido e registrado corretamente**.

---

## 2. Desafios

Pagamentos reais têm características que tornam o problema mais delicado do que parece:

### 2.1 Precisão financeira

- Um erro de **1 centavo** já é um problema grave.
- Não pode haver diferença entre:

  - O que foi cobrado
  - O que foi distribuído
  - O que foi registrado no sistema

### 2.2 Idempotência

- Em sistemas distribuídos, **requisições podem ser repetidas** (timeout, retry, falha de rede).
- Repetir a mesma requisição **não pode gerar pagamentos duplicados**.

### 2.3 Auditoria e rastreabilidade

- É preciso saber:

  - Quanto foi cobrado
  - Quanto foi descontado de taxa
  - Quanto cada pessoa recebeu

- Isso é essencial para:

  - Conciliação financeira
  - Suporte
  - Auditorias

### 2.4 Arquitetura orientada a eventos

- Sistemas modernos não fazem tudo “na mesma hora”.
- Ao confirmar um pagamento, o sistema **registra um evento** dizendo:

  > “Um pagamento foi capturado”

- Outros sistemas podem reagir a esse evento depois.

---

## 3. Objetivo

Construir uma **API pequena em Django** que simula esse núcleo de pagamentos.

Ela deve:

1. Calcular taxas da plataforma
2. Calcular o valor líquido
3. Dividir o dinheiro entre recebedores (split)
4. Persistir essas informações
5. Registrar um evento de pagamento capturado

---

## 4. Fluxo principal

1. O cliente envia uma requisição dizendo:

   - Quanto foi pago
   - Qual o método de pagamento
   - Em quantas parcelas
   - Quem vai receber e em qual proporção

2. A API:

   - Calcula a **taxa da plataforma**
   - Calcula o **valor líquido**
   - Divide esse valor entre os recebedores
   - Salva o pagamento
   - Salva os lançamentos financeiros (ledger)
   - Registra um evento de pagamento

---

## 5. Regras de negócio explicadas

### 5.1 Taxas da plataforma

A taxa depende do método de pagamento:

- **PIX**

  - Taxa: **0%**

- **Cartão – 1 parcela**

  - Taxa: **3,99%**

- **Cartão – 2 a 12 parcelas**

  - Taxa base: **4,99%**
  - **2% para cada parcela extra**

Exemplo:

- Cartão 3x:

  - 4,99% + 4% = **8,99%**

- Cartão 12x:

  - 4,99% + 22% = **26,99%**

---

### 5.2 Split de recebíveis

Depois de descontar a taxa da plataforma:

- O valor líquido é dividido entre:

  - 1 até 5 recebedores

- Cada recebedor tem:

  - Um papel (ex: produtor, afiliado)
  - Um percentual

- Regras obrigatórias:

  - A soma dos percentuais deve ser **100%**
  - O total distribuído deve bater **exatamente** com o valor líquido

---

### 5.3 Precisão e arredondamento

- Dinheiro não pode ser tratado como `float`
- Representar dinheiro usando `Decimal` (Python)
- Quantizar sempre para **2 casas decimais**
- Se, ao dividir, sobrar um ou mais centavos, o restante deve:

  - Ser atribuído **ao recebedor com o maior percentual de split**.
  - Caso haja empate de percentuais, o primeiro recebedor da lista (ordem de entrada) é utilizado como critério de desempate, garantindo determinismo.

---

### 5.4 Idempotência

O endpoint principal aceita um header:

```
Idempotency-Key
```

Regras:

- **Mesma chave + mesmo payload**

  - Retorna exatamente a mesma resposta
  - Não cria novos registros

- **Mesma chave + payload diferente**

  - Retorna erro (409 Conflict)
  - Explica que a chave já foi usada com outro conteúdo

Isso evita pagamentos duplicados.

---

## 6. Endpoints da API

### 6.1 Confirmar pagamento (persiste dados)

```
POST /api/v1/payments
```

Esse endpoint:

- Executa todos os cálculos
- Salva o pagamento
- Cria os lançamentos financeiros
- Registra o evento de pagamento capturado

A resposta devolve:

- Valores brutos, taxas e líquido
- Quanto cada recebedor vai receber
- O evento gerado

---

### 6.2 Simular cálculo (não persiste dados)

```
POST /api/v1/checkout/quote
```

Esse endpoint:

- Recebe o mesmo payload
- Faz os mesmos cálculos
- **Não salva nada no banco**

Serve para:

- Simular um checkout
- Mostrar valores antes da confirmação

---

## 7. Persistência (banco de dados)

### Payment

Representa o pagamento confirmado:

- Status
- Valores (bruto, taxa, líquido)
- Método de pagamento
- Parcelas
- Idempotency key
- Datas

---

### LedgerEntry

Representa **quem recebeu o quê**:

- Referência ao pagamento
- Recebedor
- Papel
- Valor recebido

---

### OutboxEvent

Representa um evento que será publicado depois:

- Tipo do evento (`payment_captured`)
- Payload
- Status
- Datas

Esse padrão simula integração com outros sistemas.

---

## 8. Validações obrigatórias

A API deve impedir dados inválidos, como:

- Percentuais que não somam 100%
- Mais de 5 recebedores
- Parcelamento com PIX
- Parcelas fora do intervalo permitido
- Valor zero ou negativo
- Moeda não suportada

---

## 9. Testes automatizados

Os testes devem focar em **riscos reais**, como:

- Cálculo correto de taxas
- Split correto
- Fechamento exato de centavos
- Comportamento de idempotência
