# python-yandex-cloud-functions
University project with Yandex Cloud

**Фамилия: Валеев**   
**Имя: Карим**  
**Группа: 11-903**  

## Запуск системы
1. Загрузите фотографию формата .jpg и весом менее 1 мб в Object Storage `itis-2022-2023-vvot29-photos`
2. Напишите боту [vvot29-boot](https://t.me/vvot29_boot_bot) команду из списка:   
/start   
/help  
/getface   
/find {name}


## Описание кода системы  
В папке `functions` находятся облачные функции а также файл с необходимыми им зависимостями.  
В папе `container` находится все необходимое для сборки образа, который с помощью комманд  
```
docker build --tag cr.yandex/crp17g112rfmopq8gel6/vvot29-face-cut:latest . 
docker push cr.yandex/crp17g112rfmopq8gel6/vvot29-face-cut:latest
```  
можно отправить в Container Registry.  
Остальные файлы нужны для линтеров и GitHub репозитория.

## Использованные облачные сервисы
1. itis-2022-2023-vvot29-photos - Object Storage
2. vvot29-photo-trigger - Cloud Function Trigger for Object Storage 
3. vvot29-face-detection - Cloud Function 
4. vvot29-tasks - Message Queue 
5. vvot29-task-trigger - Cloud Function Trigger for Message Queue and Serverless Containers 
6. vvot29-face-cut - Serverless Containers 
7. vvot29-registry - Container Registry 
8. itis-2022-2023-vvot29-faces - Object Storage 
9. vvot29-db-photo-face - Managed Service for YDB 
10. itis-2022-2023-vvot29-api - API Gateway 
11. vvot29-boot - Cloud Function


