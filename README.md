# Blue Check SERVICE
### Bluecarbon Surveillence Service with Sentinel Satellite

<p align="center">
  <img src="streamlit/logo/bluecheck_mainpage_logo.gif" alt="mainpage_logo"/>
</p>

# Introductions
<br>

### Detecting changes in Sentinel Imagery

1. Timelapse
   [![타임랩스](https://github.com/gunwoda/SAR-Bluecarbon-Service/assets/38150072/306a7911-5029-438e-9f72-c64fc1a446ad)](https://private-user-images.githubusercontent.com/38150072/286486008-1a257873-b362-47a1-b08d-28be2f992130.gif?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTEiLCJleHAiOjE3MDEyMzU4ODMsIm5iZiI6MTcwMTIzNTU4MywicGF0aCI6Ii8zODE1MDA3Mi8yODY0ODYwMDgtMWEyNTc4NzMtYjM2Mi00N2ExLWIwOGQtMjhiZTJmOTkyMTMwLmdpZj9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFJV05KWUFYNENTVkVINTNBJTJGMjAyMzExMjklMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjMxMTI5VDA1MjYyM1omWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTUyNTI2YTY4ZmM0ZDEzMTcwMjg4MzViNzA3Mzg3Zjc4YzYwMmE5NTZmOGJiMDZhYTI5YmM0NTIwMWQ1NmRiMjEmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JmFjdG9yX2lkPTAma2V5X2lkPTAmcmVwb19pZD0wIn0.119RhSN3TEt0mJCrJVXUjVoyh3AwFy5EKtVhroAeeng)
2. Change Detection
   ![변화탐지](https://github.com/gunwoda/SAR-Bluecarbon-Service/assets/38150072/cdd3d288-474c-4db4-99a6-3dcedce716eb)
3. Bitemporl Change Detection
   ![시계열변화탐지](https://github.com/gunwoda/SAR-Bluecarbon-Service/assets/38150072/687f19a8-610a-425d-aade-4273d70dac3e)
4. Time-Series Trend Analisis
   ![시계열경향성분석](https://github.com/gunwoda/SAR-Bluecarbon-Service/assets/38150072/102c09b1-9d91-4395-a7e6-f9a58132203b)
5. Extent Change Detection
   ![면적변화탐지](https://github.com/gunwoda/SAR-Bluecarbon-Service/assets/38150072/e6fe10f1-b565-4a35-949a-790c96383d9b)
6. AOI Managing    


# Tool
<br>
<img width="1226" alt="스크린샷 2023-11-29 오전 10 57 31" src="https://github.com/gunwoda/SAR-Bluecarbon-Service/assets/38150072/e8be5914-3a77-4e15-b14d-8b150681b07e">


# Development Period
<br>

#### Version1: 2023.10.23 ~ 2023.11.29
#### Version2(Add LLM, more AOI, and new skill): 2023.12.01 ~ 2023.12.31
#### Version3: 2024.01.01 ~

# Contributor
<br>

<table>
  <tr>
    <!-- first -->
    <td align="center">
      <a href="https://github.com/Mujae">
        <img src="https://github.com/Mujae.png" width="100px;" alt="박무재"/><br />
        <sub><b>박무재</b></sub>
      </a>
    </td>
    <!-- second -->
    <td align="center">
      <a href="https://github.com/Ojung-ii">
        <img src="https://github.com/Ojung-ii.png" width="100px;" alt="오정현"/><br />
        <sub><b>오정현</b></sub>
      </a>
    </td>
    <!-- third -->
    <td align="center">
      <a href="https://github.com/gunwoda">
        <img src="https://github.com/gunwoda.png" width="100px;" alt="김건우"/><br />
        <sub><b>김건우</b></sub>
      </a>
    </td>
    <!-- fourth -->
    <td align="center">
      <a href="https://github.com/damii1207">
        <img src="https://github.com/damii1207.png" width="100px;" alt="류다미"/><br />
        <sub><b>류다미</b></sub>
      </a>
    </td>
    <!-- fifth -->
    <td align="center">
      <a href="https://github.com/osgeokr">
        <img src="https://avatars.githubusercontent.com/u/52292818?v=4" width="100px;" alt="류다미"/><br />
        <sub><b>유병혁</b></sub>
      </a>
    </td>
  </tr>
</table>




# How to run
<br>

```bash
pip install -r requirements.txt
```

```bash
cd streamlit
streamlit run main.py
```

# Reference
<br>

1. Earth Engine Documentation: https://developers.google.com/earth-engine/apidocs
2. Google Earth Engine community: https://developers.google.com/earth-engine/tutorials
3. Streamlit Documentation: https://docs.streamlit.ioGoogle
4. Vegetation Index: https://www.mdpi.com/2072-4292/10/7/1140, https://ieeexplore.ieee.org/abstract/document/10068770
