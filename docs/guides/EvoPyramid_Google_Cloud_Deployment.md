# ☁️ Развёртывание EvoPyramid-AI на Google Cloud

> 🔺 **Принцип EvoPyramid:** «Инфраструктура — это продолжение когнитивного поля. Развёртывая код, мы расширяем сам организм, а не просто загружаем контейнер».

Этот гайд описывает пошаговый путь запуска API и вспомогательных сервисов EvoPyramid-AI в экосистеме Google Cloud. Он объединяет практики EvoCodex (PACE: Plan → Apply → Check → Elevate) и специфику облачной платформы.

## 0. Предварительные условия

| Шаг | Действие | Зачем |
| --- | --- | --- |
| 0.1 | Активируйте проект в [Google Cloud Console](https://console.cloud.google.com/). | Все ресурсы будут связаны с выбранным проектом. |
| 0.2 | Установите [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) ≥ 441.0. | Позволит автоматизировать развёртывание. |
| 0.3 | Убедитесь, что `gcloud auth login` и `gcloud config set project <ID>` выполнены. | Зафиксирует контекст для команд. |
| 0.4 | Клонируйте репозиторий: `git clone https://github.com/AleeexTk/evopyramid-ai` и перейдите в директорию. | Подготовит кодовую базу EvoPyramid. |
| 0.5 | Проверьте доступность Docker/Podman локально (Cloud Build также поддерживает удалённый билд). | Для сборки контейнеров API. |

## 1. Сборка контейнера API

API находится в `apps/api/main.py` и использует FastAPI с настройками из `apps/api/config.py`. Базовый Dockerfile можно создать в корне проекта:

```dockerfile
# docker/Dockerfile.api
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt requirements_context.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements_context.txt

COPY . .
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

> 🧠 Параметры CORS и списка доверенных хостов регулируются через переменные окружения, которые читает `APISettings`.

### 1.1 Локальная проверка контейнера

```bash
gcloud auth configure-docker
docker build -f docker/Dockerfile.api -t gcr.io/$GOOGLE_CLOUD_PROJECT/evopyramid-api:latest .
docker run -p 8080:8080 --env-file .env gcr.io/$GOOGLE_CLOUD_PROJECT/evopyramid-api:latest
```

Проверьте эндпоинт `http://localhost:8080/health` — вы должны получить `{"status": "healthy"}`.

## 2. Развёртывание через Cloud Run (рекомендуемый старт)

Cloud Run подходит для stateless FastAPI-сервисов и поддерживает авто-масштабирование.

1. Включите API:
   ```bash
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com
   ```
2. Отправьте образ в Artifact Registry или Container Registry. Пример для Artifact Registry (рекомендуется):
   ```bash
   gcloud artifacts repositories create evopyramid-repo \
       --repository-format=docker --location=us-central1 --description="EvoPyramid containers"
   gcloud auth configure-docker us-central1-docker.pkg.dev
   docker tag gcr.io/$GOOGLE_CLOUD_PROJECT/evopyramid-api:latest \
       us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/evopyramid-repo/evopyramid-api:latest
   docker push us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/evopyramid-repo/evopyramid-api:latest
   ```
3. Запустите сервис:
   ```bash
   gcloud run deploy evopyramid-api \
       --image us-central1-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/evopyramid-repo/evopyramid-api:latest \
       --region=us-central1 \
       --allow-unauthenticated \
       --set-env-vars "ENVIRONMENT=cloud,TRUSTED_HOSTS=localhost,127.0.0.1,evopyramid.com" \
       --port=8080
   ```
4. Сохраните URL, который вернёт команда. Проверьте `/api/health` и `/api/metrics` через HTTPS.

> 📈 Добавьте Stackdriver Logging и Monitoring для наблюдения за метриками. Cloud Run автоматически интегрирован с Cloud Logging.

## 3. Vertex AI для моделей и пайплайнов

Если вам требуется обучать/разворачивать модели EvoPyramid:

1. Соберите Docker-образ, содержащий `apps/core` и нужные зависимости (на базе CUDA или CPU).
2. Опубликуйте образ в Artifact Registry.
3. Создайте Vertex AI Custom Job или Model (через UI или CLI), указав образ и команду запуска.
4. Для онлайн-предсказаний используйте Vertex Endpoints, подключив API-слой как клиент.

> 🔁 В `scripts/start_local.sh` показан процесс подготовки окружения и запуска наблюдателей. Его можно перенести в Vertex AI batch jobs для оркестрации аналитических задач.

## 4. Google Kubernetes Engine (если нужен контроль)

1. Создайте кластер: `gcloud container clusters create evopyramid-gke --region=us-central1`.
2. Создайте манифесты `Deployment` и `Service` для FastAPI (реплики, ресурсы, secrets).
3. Интегрируйте `ConfigMap`/`Secret` для переменных `APISettings`.
4. Экспонируйте сервис через HTTP Load Balancer или Ingress с ManagedCertificate.

GKE полезен, если планируете несколько микросервисов EvoPyramid (например, `apps/bridge`, `apps/web_agent`).

## 5. CI/CD c Cloud Build

1. Добавьте `cloudbuild.yaml` в корень репозитория:
   ```yaml
   steps:
     - name: gcr.io/cloud-builders/docker
       args: ["build", "-f", "docker/Dockerfile.api", "-t", "us-central1-docker.pkg.dev/$PROJECT_ID/evopyramid-repo/evopyramid-api:$COMMIT_SHA", "."]
     - name: gcr.io/cloud-builders/docker
       args: ["push", "us-central1-docker.pkg.dev/$PROJECT_ID/evopyramid-repo/evopyramid-api:$COMMIT_SHA"]
   images:
     - us-central1-docker.pkg.dev/$PROJECT_ID/evopyramid-repo/evopyramid-api:$COMMIT_SHA
   ```
2. Настройте триггер на GitHub. После каждого коммита образ будет опубликован автоматически.
3. Дополнительно вызовите `gcloud run deploy` через отдельный шаг или Cloud Deploy.

### 5.1 Cloud Deploy — автоматизация шага Elevate

> ♾️ **PACE Elevate:** когда образ готов и тесты пройдены, Cloud Deploy поднимает релиз из стадии Chronos (коммит) в Kairos (рабочая среда), сохраняя трассируемость.

1. Отрендерите pipeline под ваш проект. Шаблон хранится в `clouddeploy/templates/delivery-pipeline.yaml.tpl` и рендерится скриптом, который принимает имена Cloud Run сервисов как параметры окружения:
   ```bash
   PROJECT_ID=your-project-id \
   REGION=us-central1 \
   STAGING_SERVICE=evopyramid-api-staging \
   PRODUCTION_SERVICE=evopyramid-api \
   scripts/render_clouddeploy.sh
   ```
   Результат появится в `clouddeploy/rendered/delivery-pipeline.yaml`.
2. Примените pipeline и цели окружений:
   ```bash
   gcloud deploy apply \
       --file clouddeploy/rendered/delivery-pipeline.yaml \
       --region=${REGION} \
       --project=${PROJECT_ID}
   ```
3. Подготовьте Cloud Build trigger на `cloudbuild.yaml`. Он собирает образ, публикует его в Artifact Registry, автоматически рендерит и применяет pipeline, а затем создаёт релиз через Cloud Deploy, используя `skaffold.yaml` для маппинга образа к сервисам Cloud Run. При необходимости переопределите имена сервисов через substitutions `_STAGING_SERVICE` и `_PRODUCTION_SERVICE`.
4. Для ручного (или расследовательского) запуска полного цикла используйте `scripts/trigger_cloud_build.sh`. Он собирает все substitutions, вычисляет тег образа и вызывает `gcloud builds submit`, что позволяет подтвердить прохождение Cloud Deploy стейджей без ожидания git-триггера. Скрипт проверяет наличие авторизованного аккаунта в gcloud и допускает переопределение бинаря через `GCLOUD_BIN` (например, при использовании локального SDK в нестандартном пути):
   ```bash
   PROJECT_ID=your-production-project \
   REGION=us-central1 \
   STAGING_SERVICE=evopyramid-api-staging \
   PRODUCTION_SERVICE=evopyramid-api \
   scripts/trigger_cloud_build.sh
   ```
   Добавьте `IMAGE_TAG` для фиксации конкретного релиза или `DRY_RUN=1`, чтобы проверить формируемую команду без фактического запуска. Если требуется альтернативный путь к CLI, задайте `GCLOUD_BIN=/custom/path/gcloud`.

Все параметры по умолчанию (регион, имена сервисов) задаются в `skaffold.yaml` и могут быть переопределены через профили `staging` и `production`.

## 6. Безопасность и секреты

- Используйте [Secret Manager](https://cloud.google.com/secret-manager) и задавайте переменные через `--set-secrets` в Cloud Run.
- Ограничьте входящий трафик Cloud Run с помощью VPC egress и Identity Aware Proxy, если API не публичный.
- Обновляйте зависимости (`requirements*.txt`) перед релизами и мониторьте CVE.

## 7. Заключительный чек-лист EvoCodex

| Состояние | Проверка |
| --- | --- |
| ☐ | Контейнер собран и прошёл локальный smoke-тест (`/health`). |
| ☐ | Образ загружен в Artifact Registry. |
| ☐ | Cloud Run/Vertex/GKE сервисы получают переменные окружения из Secret Manager. |
| ☐ | Логирование и мониторинг активированы. |
| ☐ | Настроен CI/CD-триггер Cloud Build. |

---

🧭 **Рефлексия:** после первого запуска зафиксируйте параметры в `EVO_SYNC_MANIFEST.yaml` (раздел инфраструктуры), чтобы архитектура помнила точку синхронизации. Следующий шаг — автоматизировать обновление с помощью Cloud Deploy и интегрировать наблюдателей из `apps/core` для облачного мониторинга.
