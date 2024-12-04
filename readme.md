# 오픈소스SW 프로젝트 1대1 단어맞추기 게임

## 주요 기술 스택  
- **Kubernetes**: 애플리케이션 컨테이너 오케스트레이션  
- **Docker**: 컨테이너 이미지 빌드 및 실행  
- **Flask**: 백엔드 웹 프레임워크  
- **HTML/JavaScript**: 프론트엔드 구현  
- **Redis**: 사용자 인증 및 세션 관리

---

## 실행 전 준비 사항  
1. **Minikube 설치** 

2. **Docker 설치**  
   Docker를 설치하여 컨테이너 이미지를 빌드합니다.  

3. **kubectl 설치**  
   Kubernetes CLI 도구인 `kubectl`을 설치하여 클러스터를 관리합니다.

---

## 실행 방법  

Kubernetes 클러스터 준비 (Minikube 실행)
```bash
minikube start
```
Kubernetes 리소스 배포
```bash
kubectl apply -f kubernetes/
```
서비스 확인
```bash
kubectl get pods
kubectl get svc
```
서비스 실행 (서비스가 정상적으로 작동하는지 확인한 후 명령어 실행)
```bash
minikube service flask-service
```

## 종료 방법
```bash
kubectl delete -f kubernetes/
```