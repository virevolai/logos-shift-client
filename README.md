![Tests](https://github.com/virevolai/logos-shift-client/actions/workflows/test_and_build.yml/badge.svg)

---

# Logos Shift

**Train and Shift your Logos Brain (LLM)**

Integrating Large Language Models (LLMs) into production systems can be a convoluted process, with myriad challenges to overcome. While several tools offer call instrumentation, **Logos Shift** sets itself apart with its game-changing feature: **automated rollout of your fine-tuned model**. Just integrate with a single line of code and let us notify you when your fine-tuned model is ready for deployment.

You can also do this yourself for free. LogosShift is the simplest and best way to do this for hackers.

Pssst: Can do this for any API, not just LLMs


## Key Feature

- **Effortless A/B Rollout**: Once your fine-tuned model achieves readiness, it's rolled out as an A/B test. No manual intervention, no complex configurations. Just simplicity.

## Other Features

- **No Proxying**: Direct calls, eliminating the latency of proxying.
- **Retain Your OpenAI Key**: Your OpenAI key remains yours, safeguarding confidentiality. No leaked keys.
- **Feedback-Driven Finetuning**: Refine model performance with feedback based on unique result IDs.
- **Open Source**: Flexibility to modify and adapt as needed.
- **Dynamic Configuration**: Synchronize with server configurations on-the-fly.
- Simplicity: Simple is beautiful. Minimal dependancies.
- No lock-in: Can optionally save data to local drive if you want to train model yourself.
- **Upcoming**:
    - Error fallback mechanisms

## Why

![sergey](assets/images/sergey.png)

At [Bohita](https://bohita.com), our pioneering efforts in deploying Large Language Models (LLMs) in production environments have brought forth unique challenges, especially concerning cost management, latency reduction, and optimization. The solutions available in the market weren't adequate for our needs, prompting us to develop and subsequently open-source some of our bespoke tools.

On the subject of proxying: We prioritize the reliability and uptime of our services. By introducing an additional domain as a dependency, we'd inherently be reducing our uptime. Specifically, the probability of combined uptime would be \(1 - (P_A\_up\_B\_down + P_B\_up\_A\_down + P_both\_down)\), which is inherently less than the uptime of either individual service. Given the inherent unpredictability of APIs in today's landscape, compromising our reliability in this manner is not a trade-off we're willing to make.

## Getting Started

### Prerequisites

- Obtain an API key from [Bohita Logos Shift Portal](https://api.bohita.com).

### Installation

```bash
pip install logos_shift_client
```

### Basic Usage

```python
from logos_shift_client import LogosShift

# Initialize with your API key (without if you just want the local copy)
logos_shift = LogosShift(api_key="YOUR_API_KEY")

# Instrument your function
@logos_shift()
def add(x, y):
    return x + y

result = add(1, 2)

# Optionally, provide feedback
logos_shift.provide_feedback(result['bohita_logos_shift_id_123', "success")
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

## Dataset

All function calls are grouped into datasets. Think of this as the usecase those calls are made for.
If you are intrumentating just one call, then you don't need to do anything. The default dataset is 'default'.

If you have different usecases in your application (E.g, chatbot for sales, vs chatbot for help), you should separate them out.

```python
@logos_shift(dataset="sales")
def add_sales(x, y):
    return x + y

@logos_shift(dataset="help")
def add_help(x, y):
    return x + y
```

This helps you track them separately and also finetune them separately for each use case.

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

## Local Copy

Initialize with a filename to keep a local copy. You can also run it without Bohita, just set api_key to None

```python
logos_shift = LogosShift(api_key="YOUR_API_KEY", filename="api_calls.log")

# Can also disable sending data to Bohita. However, you will lose the automatic routing.
logos_shift = LogosShift(api_key=None, filename="api_calls.log")
```


## Best Practices

When using Logos Shift to integrate Large Language Models (LLMs) into your applications, it’s crucial to tailor the integration to the specific outputs and outcomes that are most relevant to your use case. Below are some best practices to help you maximize the effectiveness of Logos Shift.

### Focus on Relevant Outputs

When instrumenting your functions with Logos Shift, aim to return the specific parts of the output that are most pertinent to your application’s needs.

#### Not Recommended:

```python
@logos_shift(dataset="story_raw")
def get_story(model, messages):
    """Generates a story"""
    completion = openai.ChatCompletion.create(model=model, messages=messages)
    return completion
```

In the above example, the entire completion object is returned, which might include a lot of information that is not directly relevant to your application.

#### Recommended:

```python
@logos_shift(dataset="story")
def get_story(model, messages):
    """Generates a story"""
    completion = openai.ChatCompletion.create(model=model, messages=messages)
    result = completion.to_dict_recursive()
    story_d = {'story': result['choices'][0]['message']}
    return story_d
```

In this improved version, the function returns a dictionary with just the story part of the completion. This approach ensures that the data captured by Logos Shift is more concise and directly related to your application's primary function.

### Providing Feedback

Providing feedback on specific outcomes is crucial for fine-tuning your models and ensuring accurate A/B test rollouts.

```python
story_d = get_story()
# ... your application logic ...
logos_shift.provide_feedback(story_d['bohita_logos_shift_id'], "success")
```

In this example, `provide_feedback` is called with the result ID and an outcome string ("success" in this case). This helps in two ways:

1. **Accurate A/B Test Measurements**: The feedback ensures that the A/B test rollouts are based on actual outcomes, providing a true measure of the model’s performance in real-world scenarios.
2. **Targeted Fine-Tuning**: By providing feedback on specific outcomes, you help in fine-tuning the model to better suit your application’s needs, leading to more effective and efficient model performance over time.

Adopting these best practices will help you leverage the full potential of Logos Shift, ensuring that your integration with LLMs is not just seamless but also highly effective and _outcome-driven_.

## Contribute

Feel free to fork, open issues, and submit PRs. For major changes, please open an issue first to discuss what you'd like to change.

## License

This project is licensed under the MIT License.
