Installation Guide
==================

To install the CSR Report Storage system, follow these steps:

1. Clone the repository:
   .. code-block:: bash

      git clone https://github.com/RuiZhao233/ift_coursework_2024_Wisteria.git
      cd ift_coursework_2024_Wisteria

2. Install dependencies:
   .. code-block:: bash

      pip install -r requirements.txt

3. Set up MinIO and PostgreSQL using Docker:
   .. code-block:: bash

      docker-compose up --build

      