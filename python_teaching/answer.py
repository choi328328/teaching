"""
Computer의 탄생 : 
	계산하기 싫다...대신 계산해줘


Computing의 목적 :
	나대신 일해주는 누군가
	돈 많으면? -> 고용해서 써라
	돈 없으면? -> 노트북 + 자동화 하나면 가능
	NASA 달 탐사 컴퓨터 > 아이폰 SE
 

Python :
	다용도 목적의 언어
	모든 Task를 2번째로 잘하는 언어
	Guido Van Rossum이라는 분이 제작함
	Python Monty의 모험이라는 아주 유명한 코미디 프로그램에서 이름을 따옴...
	Python은 뱀이라는 의미도 있어서 파이썬 관련 코드들엔 뱀그림을 심심치않게 볼 수 있음


Teaching의 목적 : 
	Efficient work = 날먹
	날먹을 잘할 수록 일을 잘하는 것
	코딩을 효율적으로 하면 날먹 가능
	좋은 코딩이 뭔지 공부하려면 파이썬을 해보는게 좋음...
	R은 좋은 코딩을 보여줄만한 코드가 별로 없음...통계학용 코드이기 때문에 딱히 프로그래머들이 관심이 없어서...


What is IDE? :
	Rstudio, Visual studio code
	프로그래밍에 도움을 주는 프로그램
	Vscode 강추
 

What is Env?:
	여러가지 library, package들이 깔려서 특정 프로그램들을 구성하기 위한 환경을 갖춘것.
	
	만약 A라는 분석이 X라는 프로그램의 version 0.1을 사용하는데...
	B라는 새로운 분석할일이 생기면서 X라는 프로그램의 Version 1.0을 써야한다?
 	그냥 컴퓨터 os에 바로 library, package 깔면...? -> A 분석이 안돌아감
	CDM은 맨날 쓰이는 패키지가 똑같으니까 별 문제 안됨
	
	딥러닝이나 기타 여러가지 분석할 때는 큰 문제가 된다
 	Anaconda가 대표적으로 가상환경을 만들어줌 @note
 
 
What is API? :
	Application Programming Interface
	어떤 프로그램과 소통하는 방식인데... 많은 곳에서 Open API를 제공함(구글, 네이버)
 
 
What is Terminal?:
	리눅스나 맥에서 컴퓨터 os 단과 직접 소통하기 위한 연결창구 
 
 
What is Good code?:
	Readable, reusable, maintainable
	-> Refactoring이 매우 중요함 (Green-Yello-Red)


Purpose : 
	코딩 짜는 프로세스를 효율적으로 만들어 봅시다.
 	여러분들이 하는 일을 반-자동화해봅시다.
	여러분들이 하는 일의 로그를 남기고, 마우스 사용을 최대한 줄여봅시다.

"""

# 1-1. Web API automation

"""
모든 코딩에 앞서 먼저 슈도 코드를 작성하는 습관을 들임

Dataclass 및 xml, json, yaml 개념을 확인함

1. 먼저 목적을 적음
2. 전체적인 개요를 작성함
3. 각 흐름을 함수화함. (나중에 고수가 되면 클래스화 하세요)

목적 : 
	구글 캘린더 일정 업데이트를 위한 폴더를 제작함
	
"""

# 1-2. Web API automation

"""
목적 : 
	구글 캘린더 automation을 위한 seminar_automator class를 제작함
	class method : 업데이트

"""

# 2. Logging을 진행해보자

"""
목적 : 
	Web API를 만들 때 로깅을 진행해보기


"""

# 3. Atlas Automation

"""

목적 : 
ATLAS에서 PLP를 짜서 다운로드 받고 자동으로 서버에서 실행되고 결과알림

Flow : 
	1. ATLAS 다운로드 받음 as zipfile
	2. zipfile을 서버로 이동시킴
	3. 서버에서 zipfile을 해제
	4. Config 설정 
	5. PLP 실행
	6. 결과 확인

"""

# 4. Automation for Lab

"""

목적 : 
Lab에서 자주 반복되는 업무 혹은 개인적인 업무들에 대한 automation을 실시

Flow : 
	1. ?

"""

if __name__ == "__main__":
    # atlas_download_as_zipfile(ple_num, zipfile_path)
    # zipfile_to_server(zipfile_path, server_path)
    # unzip(server_path)
    # plp_config_set(ID, PW, CDM)
    # run_plp(plp_path)
    pass


# 5. Packing for Reusable code

"""

목적 : 
작성한 automation 코드를 재사용을 위해 package화 진행

Flow : 


"""
