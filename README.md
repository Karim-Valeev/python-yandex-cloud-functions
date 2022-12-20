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


