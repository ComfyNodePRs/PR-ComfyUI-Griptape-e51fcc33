import os
import folder_paths
import base64
import torch
from PIL import Image, ImageOps, ImageSequence
import numpy as np
from io import BytesIO
from jinja2 import Template


def get_prompt_text(string_prompt, input_string):
    template = Template(string_prompt)
    return template.render(input_string=input_string)


def image_path_to_output(image_path):
    img = Image.open(image_path)
    output_images = []
    output_masks = []
    for i in ImageSequence.Iterator(img):
        i = ImageOps.exif_transpose(i)
        if i.mode == "I":
            i = i.point(lambda i: i * (1 / 255))
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        if "A" in i.getbands():
            mask = np.array(i.getchannel("A")).astype(np.float32) / 255.0
            mask = 1.0 - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
        output_images.append(image)
        output_masks.append(mask.unsqueeze(0))

    if len(output_images) > 1:
        output_image = torch.cat(output_images, dim=0)
        output_mask = torch.cat(output_masks, dim=0)
    else:
        output_image = output_images[0]
        output_mask = output_masks[0]
    return (output_image, output_mask)


def convert_tensor_to_base_64(image):
    if isinstance(image, torch.Tensor):
        # Convert to base64
        print("Converting to base64")

        # Ensure it's on CPU and remove batch dimension if there's one
        if image.dim() == 4 and image.shape[0] == 1:
            image = image.squeeze(0)  # Removes batch dimension if it's 1

        # Permute the dimensions if necessary (from C, H, W to H, W, C)
        if image.shape[0] < image.shape[2]:  # Assuming channel-first ordering
            image = image.permute(1, 2, 0)  # Change to (Height, Width, Channels)

        # Scale to 0-255 and convert to uint8
        image = (255.0 * image).clamp(0, 255).numpy().astype(np.uint8)

        # Create PIL Image from array
        img = Image.fromarray(image)

        # Save the image to a buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # Encode to base64
        final_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        print("Base64 Conversion Successful")
        return final_image
    else:
        return None
