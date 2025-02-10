
# Raporting API

# -> Generate Specification based on prompts
# -> Generate Summariztion of something based on prompts


# CI/CD

Adding service account
Adding permissions for new repository

gcloud config set account voicesense@voicesense.iam.gserviceaccount.com

gcloud auth configure-docker \
    europe-central2-docker.pkg.dev


-- Run this command to grant the roles/artifactregistry.writer permission:

gcloud artifacts repositories add-iam-policy-binding raporting \
  --location=europe-central2 \
  --project=voicesense \
  --member="allUsers" \
  --role="roles/artifactregistry.writer"