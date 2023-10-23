---

# Logos Shift

Logos Shift is an open-source library designed to instrument your calls without adding latency. Integrate it with your existing systems, and gain insights into the function's input, output, and associated metadata.

This is designed to switch your expensive model with a fine tuned model

## Features

- **No Proxying**: Direct calls without the overhead of proxying, ensuring no additional latency.
- **Keep Your OpenAI Key**: We don't need access to your OpenAI key. Ensure it stays confidential and with you.
- **Feedback Support**: Provide feedback on whether a result was successful or not based on its unique ID. This is used to have better finetunes for your model.
- **Truly Open Source**: Extend and modify as per your requirements.
- **Upcoming Features**:
  - Dynamic configuration from the server.

## Why

![sergey](assets/images/sergey.png)

## Getting Started

### Prerequisites

- Obtain an API key from [Bohita Logos Shift Portal](https://bohita.com).

### Installation

```bash
pip install logos_shift_client
```

### Basic Usage

```python
from logos_shift_client import LogosShift

# Initialize with your API key
logos_shift = LogosShift(api_key="YOUR_API_KEY")

# Instrument your function
@logos_shift()
def add(x, y):
    return x + y

result = add(1, 2)

# Later, optionally, provide feedback
logos_shift.provide_feedback(result['bohita_logos_shift_id', "success")
```

## How It Works

Here's a high-level overview:

```mermaid
graph LR
    A["Client Application"]
    B["Logos Shift Client"]
    C["Buffer Manager Thread"]
    D["Logos Server"]
    E["Expensive LLM Client"]
    F["Cheap LLM Client"]
    G["API Router A/B Test Rollout"]

    A -->|"Function Call"| B
    B -->|"Capture & Buffer Data"| C
    C -->|"Send Data"| D
    B -->|"Route API Call"| G
    G -->|"Expensive API Route"| E
    G -->|"Cheap API Route"| F

    classDef mainClass fill:#0077b6,stroke:#004c8c,stroke-width:2px,color:#fff;
    classDef api fill:#90e0ef,stroke:#0077b6,stroke-width:2px,color:#333;
    classDef buffer fill:#48cae4,stroke:#0077b6,stroke-width:2px,color:#333;
    classDef expensive fill:#d00000,stroke:#9d0208,stroke-width:2px,color:#fff;
    classDef cheap fill:#52b788,stroke:#0077b6,stroke-width:2px,color:#333;

    class A,B,D,G mainClass
    class E expensive
    class F cheap
    class C buffer
```


## Metadata

You can provide additional metadata, including `user_id`, which can be used for routing decisions based on user-specific details.

```python
@logos_shift()
def multiply(x, y, logos_shift_metadata={"user_id": "12345"}):
    return x * y
```

## Feedback

Using feedback you can get better models that will be cheaper and more effective.

If you don't have feedback, it will be auto-regressive as usual.

## Configuration Retrieval

The library will also support retrieving configurations every few minutes, ensuring your logos_shift adapts to dynamic environments.

## Contribute

Feel free to fork, open issues, and submit PRs. For major changes, please open an issue first to discuss what you'd like to change.

## License

This project is licensed under the MIT License.
