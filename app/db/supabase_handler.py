import os
from supabase import create_client, Client
from fastapi import UploadFile
from fastapi import HTTPException
import uuid


# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client() -> Client:
    """
    Returns the initialized Supabase client
    """
    return supabase

def create_bucket(bucket_name: str) -> dict:
    """
    Create a storage bucket in Supabase
    
    Args:
        bucket_name: Name of the bucket to create
        
    Returns:
        Response from Supabase API
    """
    try:
        # Check if bucket already exists
        buckets = supabase.storage.list_buckets()
        if any(bucket.name == bucket_name for bucket in buckets):
            return {"message": f"Bucket '{bucket_name}' already exists"}
        
        # Create the bucket
        response = supabase.storage.create_bucket(
            id=bucket_name,
            name=bucket_name)
        return {"message": f"Bucket '{bucket_name}' created successfully", "data": response}
    
    except Exception as e:
        return {"error": str(e)}

async def upload_file(
        user_id: str,
        folder_name: str,
        bucket_name: str,
        file: UploadFile,
        overwrite: bool = False
        ) -> dict:
    """
    Upload a file to a Supabase storage bucket
    
    Args:
        bucket_name: Name of the bucket to upload to
        file: FastAPI UploadFile object
        
    Returns:
        Response from Supabase API with file URL
    """
    # Create a unique file name using UUID add folder name if provided
    if folder_name is not None:
        directory = f"{user_id}/{folder_name}"
    else:
        directory = f"{user_id}"

    # Check if the file already exists
    files = supabase.storage.from_(bucket_name).list(path=directory)
    
    # Check if the file already exists
    if any(existing_file['name'] == file.filename for existing_file in files):
        if overwrite:
            # If overwrite is True, remove the existing file
            supabase.storage.from_(bucket_name).remove([f"{directory}/{file.filename}"])
        else:
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' already exists at directory: {directory}.  Consider useing overwrite=True to replace it.")
    
    # Read file content
    file_content = await file.read()
    
    # Upload to Supabase
    upload_filepath = f"{directory}/{file.filename}"
    response = supabase.storage.from_(bucket_name).upload(
        upload_filepath,
        file_content,
        {"content-type": file.content_type}
    )
    
    return {
        "status": "successful",
        "filename": file.filename,
        "file_path": response.path,
    }

def download_file(bucket_name: str, file_path: str) -> dict:
    """
    Download a file from a Supabase storage bucket
    
    Args:
        bucket_name: Name of the bucket
        file_path: Path to the file in the bucket
        
    Returns:
        Response from Supabase API
    """
    try:
        response = supabase.storage.from_(bucket_name).download(file_path)
        return {
            "message": f"File '{file_path}' downloaded successfully", 
            "data": response
        }
    
    except Exception as e:
        return {"error": str(e)}

def delete_file(bucket_name: str, file_path: str) -> dict:
    """
    Delete a file from a Supabase storage bucket
    
    Args:
        bucket_name: Name of the bucket
        file_path: Path to the file in the bucket
        
    Returns:
        Response from Supabase API
    """
    try:
        response = supabase.storage.from_(bucket_name).remove([file_path])
        return {"message": f"File '{file_path}' deleted successfully", "data": response}
    
    except Exception as e:
        return {"error": str(e)}
    

if __name__ == "__main__":
    # Example usage
    bucket_name = "example-bucket"
    file_path = "path/to/your/file.txt"

    create_bucket(bucket_name)