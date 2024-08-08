import os
import sys
import time
import asyncio
import traceback
import google.api_core.retry as retry
import google.generativeai as genai

class VideoLLM():
  """
  VideoLLM class
  
  This class is used to take an uploaded video and obtain LLM inference results.

  """
  def __init__(self, encoded_email, entity_id, file_handler):
    """
    Constructor for VideoLLM class

    Args:
      video_path (str): Path to the video file
      prompt (str): The LLM Prompt to send alongside the video
    """
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    self.model_name = "gemini-1.5-pro-exp-0801"
    # self.model_name = "gemini-1.5-pro"
    # self.model_name = "gemini-1.5-flash"
    self.timeout = 600
    self.model = genai.GenerativeModel(model_name=self.model_name)
    model_info = genai.get_model(f"models/{self.model_name}")
    print(model_info)
    file_handler.write_to_log(encoded_email, entity_id, model_info)

  def clean_response(self, response):
    try:
      output = response.split('```html')[1]
      output = output.replace('```', '')
    except IndexError:
      output = response
    return output

  def async_process_init(self, encoded_email, entity_id, file_handler):
    asyncio.run(self.async_process_video(encoded_email, entity_id, file_handler))

  async def async_process_video(self, encoded_email, entity_id, file_handler):
    await self.process_video(encoded_email, entity_id, file_handler)

  def process_video(self, encoded_email, entity_id, file_handler):
    # TODO: Refactor to reduce nested loops
    video_dir = f'data/user_data/{encoded_email}/data/entities/{entity_id}/videos'
    all_video_filenames = os.listdir(video_dir)
    all_gemini_files = []
    entity_data = file_handler.get_entity(encoded_email, entity_id)
    business_data = f'Business Name: {entity_data.get("name")}\nBusiness Description: {entity_data.get("description")}\n'
    
    entity_data.get('description')
    for filename in all_video_filenames:
      vid_path = os.path.join(video_dir, filename)
      gemini_vid = self.upload_video_to_gemini(vid_path, encoded_email, entity_id, file_handler)
      #TODO Add caching
      all_gemini_files.append(gemini_vid)
    txt_files = []
    for file in os.listdir('data/prompts'):
      if file.endswith('.txt'):
        txt_files.append(file)
    for prompt_file in txt_files:
      prompt = ''
      with open(f'data/prompts/{prompt_file}', 'r') as f:
        prompt = business_data + f.read()
      inference_start_time = time.time()
      message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} Getting LLM inference for {prompt_file}..."
      print(message)
      file_handler.write_to_log(encoded_email, entity_id, message)
      retry_count = 0
      while True:
        output_file = prompt_file.replace('.txt', '.html')
        with open(f'data/user_data/{encoded_email}/data/entities/{entity_id}/profiles/{output_file}', 'w') as f:
          try:
            response = self.get_llm_inference(all_gemini_files, prompt)
            output = self.clean_response(response.text)
            f.write(output)
            inference_processing_seconds = int(time.time() - inference_start_time)
            message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} LLM inference for {prompt_file} completed in {int(inference_processing_seconds)} seconds."
            print(message)
            file_handler.write_to_log(encoded_email, entity_id, message)
            break
          except ValueError:
            message = f"Error writing to file: {output_file}"
            file_handler.write_to_log(encoded_email, entity_id, message)
            print(message)
            print(response)
            message = f'Retry #{retry_count} starting in 30 seconds...'
            file_handler.write_to_log(encoded_email, entity_id, message)
            print(message)
            time.sleep(30)
            retry_count += 1
          except Exception as e:
            message = f"Error: {e}"
            file_handler.write_to_log(encoded_email, entity_id, message)
            print(message)
            message = traceback.format_exc()
            file_handler.write_to_log(encoded_email, entity_id, message)
            print(message)
            message = f'Retry #{retry_count} starting in 30 seconds...'
            file_handler.write_to_log(encoded_email, entity_id, message)
            print(message)
            time.sleep(30)
            retry_count += 1
          if retry_count == 100:
            message = 'Max retries reached. Exiting...'
            file_handler.write_to_log(encoded_email, entity_id, message)
            print(message)
            break

    message = f"LLM inference completed."
    print(message)
    file_handler.write_to_log(encoded_email, entity_id, message)
    return True

  def upload_video_to_gemini(self, video_path, encoded_email, entity_id, file_handler):
    video_name = video_path.split('/')[-1]
    message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} Uploading video {video_name} to Gemini..."
    print(message)
    file_handler.write_to_log(encoded_email, entity_id, message)
    start_time = time.time()
    video_file = genai.upload_file(path=video_path)
    seconds = int(time.time() - start_time)
    message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} Completed upload: {video_file.uri} in {seconds} seconds"
    print(message)
    file_handler.write_to_log(encoded_email, entity_id, message)
    processing_time_start = time.time()
    print("Processing video...")
    while video_file.state.name == "PROCESSING":
      time.sleep(5)
      video_file = genai.get_file(video_file.name)
    processing_time = int(time.time() - processing_time_start)
    message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} Video {video_file.name} processed in: {processing_time} seconds"
    print(message)
    file_handler.write_to_log(encoded_email, entity_id, message)
    return video_file

  def get_llm_inference(self, all_gemini_files, prompt):
    """
    Function to get LLM inference results

    Returns:
      dict: LLM Inference results
    """
    all_gemini_files.append(prompt)
    response = self.model.generate_content(all_gemini_files,
                                      request_options={
                                        "timeout": self.timeout,
                                        "retry": retry.Retry(initial=45, multiplier=2, maximum=60, timeout=self.timeout)
                                        })

    return response