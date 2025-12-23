import asyncio


async def qa_execute(step: dict, prompt: str, stream: bool):
    thinking_steps = [
        f"thinking 1...step:{step['step']}",
        f"thinking 2...step:{step['step']}",
        f"thinking 3...step:{step['step']}",
        f"thinking 4...step:{step['step']}",
    ]
    final_answer = f"final_response...step:{step['step']}"

    # --- PATH A: Streaming ---
    if stream:

        async def _async_stream_generator():
            for thinking in thinking_steps:
                await asyncio.sleep(0.1)  # Non-blocking sleep
                yield {"event": "qa_thinking", "step": step["step"], "data": thinking}

            yield {"event": "final_qa", "step": step["step"], "data": final_answer}

        return _async_stream_generator()

    # --- PATH B: Non-Streaming ---
    else:
        await asyncio.sleep(2.0)
        return {"event": "final_qa", "step": step["step"], "data": final_answer}


async def reformat_execute(final_response: str, stream: bool):
    thinking_steps = [
        "reformat 1...",
        "reformat 2...",
        "reformat 3...",
        "reformat 4...",
    ]
    final_answer = f"final_response...{final_response.strip()}"
    # --- PATH A: Streaming ---
    if stream:

        async def _async_stream_generator():
            for thinking in thinking_steps:
                await asyncio.sleep(0.1)  # Non-blocking sleep
                yield {"event": "reformat_thinking", "data": thinking}

            yield {"event": "final_reformat", "data": final_answer}

        return _async_stream_generator()
    # --- PATH B: Non-Streaming ---
    else:
        await asyncio.sleep(1.0)
        return {"event": "final_reformat", "data": final_answer}


async def multistep_processing(user_prompt: str, stream: bool):
    planner_steps = [
        {"step": 1, "action": "step_1", "input": "hi1"},
        {"step": 2, "action": "step_2", "input": "hi2"},
        {"step": 3, "action": "step_3", "input": "hi3"},
    ]

    # --- PATH A: Streaming ---
    if stream:

        async def _stream_all():
            aggregated_response = ""
            for step_dict in planner_steps:
                print(f"------- Current step: {step_dict['step']} -------")
                qa_response = await qa_execute(step_dict, user_prompt, stream=True)
                qa_final_response = ""
                async for event in qa_response:
                    if event["event"] == "final_qa":
                        qa_final_response = event["data"]
                    elif event["event"] == "qa_thinking":
                        yield event
                aggregated_response += qa_final_response + " "
            # Send aggregated_response to reformat_execute
            reformat_response = await reformat_execute(aggregated_response, stream=True)
            async for event in reformat_response:
                yield event

        return _stream_all()

    # --- PATH B: Non-Streaming ---
    else:
        aggregated_response = ""
        for step_dict in planner_steps:
            print(f"------- Current step: {step_dict['step']} -------")
            qa_response = await qa_execute(step_dict, user_prompt, stream=False)
            qa_final_response = qa_response["data"]
            aggregated_response += qa_final_response + " "

        reformat_response = await reformat_execute(aggregated_response, stream=False)
        return reformat_response


async def run_agent(user_prompt: str, stream: bool):
    response = await multistep_processing(user_prompt, stream=stream)
    # --- PATH A: Streaming ---
    if stream:
        async def streaming_response():
            async for event in response:
                if event["event"] == "final_reformat":
                    to_assign_ref = event["data"]
                    new_assign_ref = to_assign_ref + "ref:1"
                    yield {"event": "final_reformat", "data": new_assign_ref}
                else:
                    yield event

        return streaming_response()
    # --- PATH B: Non-Streaming ---
    else:
        to_assign_ref = response["data"]
        new_assign_ref = to_assign_ref + "ref:1"
        return {"event": "final_reformat", "data": new_assign_ref}


# --- Function 3: The Consumer ---
async def run_server():
    user_prompt = "Explain quantum physics"
    response = await run_agent(user_prompt, stream=True)
    async for chunk in response:
        event_type = chunk["event"]
        content = chunk["data"]
        if event_type == "qa_thinking":
            print(f"🧠 [Thinking_qa]: {content}")
        elif event_type == "reformat_thinking":
            print(f"🖊️ [Formatting_qa]: {content}")
        elif event_type == "final_qa":
            print(f"✅ [Final_qa]: {content}")
        elif event_type == "final_reformat":
            print(f"🏁 [Completed]: {content}")


if __name__ == "__main__":
    asyncio.run(run_server())
