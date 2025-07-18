# smelter--cardforge
Transforming digital card designs into physical masterpieces, ready for the cutter.


Smelter is the robust backend service responsible for automating the pre-press process for custom card printing. It meticulously handles the ingestion of card lists, fetches and enhances associated image assets, performs high-quality upscaling, precisely imposes designs onto print sheets, and generates industry-standard JDF files for seamless integration with cutting machinery. This system is crucial for ensuring efficiency and precision in the physical production pipeline.

Key Features:

Image Acquisition & Management: Downloads and organizes card images from specified sources.

AI-Powered Upscaling: Enhances image resolution for high-quality print output. -- Using Upscayl -- 

Print Sheet Imposition: Arranges multiple card designs efficiently onto printable sheets.

JDF File Generation: Creates industry-standard Job Definition Format files for automated cutting.

Error Handling & Logging: Robust mechanisms for tracking and managing processing issues.

Technology Stack: Python, Flask, Image Processing Libraries (e.g., Pillow, OpenCV), JDF Library (or custom JDF generation logic).
