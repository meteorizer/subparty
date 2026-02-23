# Sub Party 
LAN 상에서 컴퓨터 간의 간단한 파일 공유를 목적으로 제작함. 
로그인이나 별도 인증 절차를 두지 않음. 

## 설치 방법
uv를 설치한 후
```
# mac, linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# windows powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" 
```

빌드하면 됨. 
```
uv run build.py
```

dist 폴더 아래의 main.dist 폴더를 복사하여 이용하거나, macos인 경우 main.app 파일을 사용하면 됨. 

## 사용 방법
실행 후, 공유하고 싶은 파일을 드래그 앤 드랍하여 등록함. 
상대편 컴퓨터에서는 다운로드 버튼을 눌러 다운로드 하고, 다운로드된 파일은 다운로드 폴더의 SubParty를 폴더에서 확인할 수 있음.