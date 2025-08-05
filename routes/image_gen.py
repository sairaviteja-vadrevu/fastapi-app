"""Image generation route."""

import os
from datetime import datetime
from typing import List, Optional
import replicate
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from bson import ObjectId
from helpers.db import get_database

load_dotenv()

router = APIRouter()

REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")

# Set the API key for replicate
if REPLICATE_API_KEY:
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY

db = get_database("images_gen")


class ImageGenerationRequest(BaseModel):
    """Model for image generation request."""

    prompt: str
    input_image: str = None
    output_format: str = "jpg"
    aspect_ratio: str = "4:3"


class Gen4ImageRequest(BaseModel):
    """Model for Gen4 image generation request."""

    prompt: str
    aspect_ratio: str = "4:3"
    reference_tags: Optional[List[str]] = None
    reference_images: Optional[List[str]] = None


def extract_url_from_output(output):
    """Extract URL string from various output types."""
    try:
        # Check if it's a FileOutput object
        if hasattr(output, "url"):
            return str(output.url)

        # Check if it's already a string
        if isinstance(output, str):
            return output

        # Check if it's a list
        if isinstance(output, list) and len(output) > 0:
            first_item = output[0]
            if hasattr(first_item, "url"):
                return str(first_item.url)
            else:
                return str(first_item)

        # Fallback
        return str(output)

    except (AttributeError, TypeError, IndexError, ValueError) as e:
        print(f"Error extracting URL: {e}")
        return str(output)


@router.post("/generate")
async def generate_image(request: ImageGenerationRequest):
    """Generate an image based on the provided prompt using Flux Kontext Pro."""
    try:
        if not REPLICATE_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="REPLICATE_API_KEY is not set in the environment variables.",
            )

        print("Generating image with Flux Kontext Pro...")

        # Prepare input for replicate
        input_data = {
            "prompt": request.prompt,
            "output_format": request.output_format,
            "safety_tolerance": 2,
            "prompt_upsampling": False,
        }

        # Only include aspect_ratio if provided
        if request.aspect_ratio:
            input_data["aspect_ratio"] = request.aspect_ratio

        # Only include input_image if provided
        if request.input_image:
            input_data["input_image"] = request.input_image

        print(f"Input data: {input_data}")

        # Run the model using replicate.run()
        # output = replicate.run("black-forest-labs/flux-kontext-pro", input=input_data)
        output = replicate.run("black-forest-labs/flux-kontext-max", input=input_data)
        # Note: Using flux-kontext-max for better performance
        # You can switch back to flux-kontext-pro if needed

        print(f"Output: {output}")

        # Extract URL from output
        output_url = extract_url_from_output(output)

        print(f"Final output URL: {output_url}")

        # Store the generated image data in MongoDB
        image_data = {
            "prompt": request.prompt,
            "input_image": request.input_image,
            "output_format": request.output_format,
            "output_url": output_url,
            "model": "black-forest-labs/flux-kontext-pro",
            "created_at": datetime.utcnow(),
            "status": "completed",
        }

        result = await db.images.insert_one(image_data)

        return {
            "image_url": output_url,
            "message": "Image generated successfully with Flux Kontext Pro",
            "success": True,
            "id": str(result.inserted_id),
        }

    except replicate.exceptions.ReplicateError as e:
        return {
            "message": f"Replicate API error: {str(e)}",
            "success": False,
            "status_code": 500,
        }


@router.post("/generate-gen4")
async def generate_gen4_image(request: Gen4ImageRequest):
    """Generate an image using RunwayML Gen4 Image model."""
    try:
        if not REPLICATE_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="REPLICATE_API_KEY is not set in the environment variables.",
            )

        print("Generating image with RunwayML Gen4...")

        # Prepare input for replicate
        input_data = {"prompt": request.prompt, "aspect_ratio": request.aspect_ratio}

        # Only include reference_tags if provided
        if request.reference_tags:
            input_data["reference_tags"] = request.reference_tags

        # Only include reference_images if provided
        if request.reference_images:
            input_data["reference_images"] = request.reference_images

        print(f"Input data: {input_data}")

        # Run the model using replicate.run()
        output = replicate.run("runwayml/gen4-image", input=input_data)

        print(f"Output: {output}")

        # Extract URL from output
        output_url = extract_url_from_output(output)

        print(f"Final output URL: {output_url}")

        # Store the generated image data in MongoDB
        image_data = {
            "prompt": request.prompt,
            "aspect_ratio": request.aspect_ratio,
            "reference_tags": request.reference_tags,
            "reference_images": request.reference_images,
            "output_url": output_url,
            "model": "runwayml/gen4-image",
            "created_at": datetime.utcnow(),
            "status": "completed",
        }

        result = await db.images.insert_one(image_data)

        return {
            "image_url": output_url,
            "message": "Image generated successfully with RunwayML Gen4",
            "success": True,
            "id": str(result.inserted_id),
        }

    except replicate.exceptions.ReplicateError as e:
        return {
            "message": f"Replicate API error: {str(e)}",
            "success": False,
            "status_code": 500,
        }


@router.get("/generations")
async def get_image_generations():
    """Retrieve all image generations from the database."""
    try:
        generations = await db.images.find(
            {}, {"_id": 1, "output_url": 1, "created_at": 1}
        ).to_list(length=None)
        if not generations:
            return {
                "message": "No image generations found.",
                "success": True,
                "generations": [],
            }

        # Convert ObjectId to string and format the created_at field
        for generation in generations:
            generation["_id"] = str(generation["_id"])

        # Return the list of generations
        generations.sort(key=lambda x: x["created_at"], reverse=True)
        return {"generations": generations, "success": True}
    except PyMongoError as e:
        return {
            "message": f"Error retrieving image generations: {str(e)}",
            "success": False,
            "status_code": 500,
        }


@router.get("/delete/{generation_id}")
async def delete_image_generation(generation_id: str):
    """Delete an image generation by ID."""
    try:
        object_id = ObjectId(generation_id)
        result = await db.images.delete_one({"_id": object_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Image generation not found.")

        return {"message": "Image generation deleted successfully.", "success": True}

    except PyMongoError as e:
        return {
            "message": f"Error deleting image generation: {str(e)}",
            "success": False,
            "status_code": 500,
        }
