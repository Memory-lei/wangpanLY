from datetime import datetime

from django.shortcuts import render,HttpResponse,redirect
from django.http import JsonResponse,StreamingHttpResponse, HttpRequest
from django.core.paginator import Paginator

import requests
import json

def index(request:HttpRequest):
    return render(request,'index.html')

#获取token，保存在django_session表中,方便每次访问API携带token
def get_token(username, password):
    data = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "domain": {"name": "default"},
                        "name": username,
                        "password": password
                    }
                }
            },
            "scope": {
                "project": {
                    "domain": {"name": "default"},
                    "name": "admin"
                }
            }
        }
    }
    url = "http://192.168.176.114:5000/v3/auth/tokens" #调用OpenStack auth接口，接口地址为http://ip:5000/v3/auth/tokens
    code = requests.post(url, data=json.dumps(data)) #json.dumps 用于将 Python 对象编码成 JSON 字符串
    return code

def login(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("u")
        passwd = request.POST.get("p")
        code = get_token(username, passwd)
        print("Status code:", code.status_code)
        if code.status_code == 201:
            request.session['user'] = username
            request.session['token'] = code.headers.get("X-Subject-Token")
            print("Login successful, redirecting to containers")
            return redirect('/containers')
        else:
            error_msg ="用户名或密码不正确，请重新登录"
            print("Login failed, rendering index with error")
            return render(request,"index.html",{
            'login_error_msg':error_msg,
        })
    else:
        print("Not a POST request, rendering index")
        return render(request, "index.html", {'login_error_msg': None})

#登录成功后，读取容器containers并分页显示在main.html中
def containers(request: HttpRequest):
    # 验证session，防止未登录访问
    if 'token' not in request.session:
        return redirect('/index')

    headers = {'X-Auth-Token': request.session['token'], "Content-Type": "application/json"}
    # 获取容器列表的接口
    containers_url = "http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665?format=json"
    containers_resp = requests.get(containers_url, headers=headers)
    containers_data = containers_resp.json()

    # 遍历每个容器，获取并转换创建时间
    for container in containers_data:
        container_name = container['name']
        # 获取容器元数据的接口（HEAD 请求）
        metadata_url = f"http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665/{container_name}"
        metadata_resp = requests.head(metadata_url, headers=headers)
        # 从响应头获取时间戳（X-Timestamp）
        timestamp = metadata_resp.headers.get('X-Timestamp')
        if timestamp:
            # 将时间戳（秒数）转换为 datetime 对象
            create_time = datetime.fromtimestamp(float(timestamp))
            container['create_time'] = create_time
        else:
            container['create_time'] = "时间获取失败"

    # 分页处理，每页 7 条数据
    paginator = Paginator(containers_data, 7)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    return render(request, 'containers.html', {'resp1': page})

#进入容器
def objects(request, data2):
    # 验证session中是否有token，防止未登录访问
    if 'token' not in request.session:
        return redirect('/index')

    # 直接从session中获取登录时保存的token
    headers = {'X-Auth-Token': request.session['token'], "Content-Type": "application/json"}

    # 构造获取对象列表的URL
    url = f"http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665/{data2}?format=json"
    resp = requests.get(url, headers=headers)
    objects_data = resp.json()

    # 分页处理，每页6条数据
    paginator = Paginator(objects_data, 6)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    return render(request, 'objects.html', {'resp1': page, 'data2': data2})

def create_container(request, container_name):
    # 验证登录状态
    if 'token' not in request.session:
        return redirect('/index')

    # 从session获取token
    headers = {
        'X-Auth-Token': request.session['token'],
        "Content-Type": "application/json"
    }

    # 调用Swift API创建容器
    url = f"http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665/{container_name}"
    response = requests.put(url, headers=headers)

    # 根据响应状态处理
    if response.status_code in [201, 202]:  # 201创建成功，202接受请求
        return redirect('/containers')
    else:
        return HttpResponse(f"创建容器失败，错误码: {response.status_code}")


def delete_object(request, container_name, object_name):
    # 验证登录状态
    if 'token' not in request.session:
        return redirect('/index')

    # 从session获取token
    headers = {
        'X-Auth-Token': request.session['token'],
        "Content-Type": "application/json"
    }

    # 调用Swift API删除文件
    encoded_object_name = requests.utils.quote(object_name)  # 处理特殊字符
    url = f"http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665/{container_name}/{encoded_object_name}"
    response = requests.delete(url, headers=headers)

    # 删除后返回原容器页面
    if response.status_code == 204:  # 204表示删除成功
        return redirect(f'/objects/{container_name}')
    else:
        return HttpResponse(f"删除文件失败，错误码: {response.status_code}")


def delete_container(request, container_name):
    # 验证登录状态，确保用户已登录
    if 'token' not in request.session:
        return redirect('/index')

    # 从session获取登录时保存的token
    headers = {
        'X-Auth-Token': request.session['token'],
        "Content-Type": "application/json"
    }

    # 调用Swift API删除容器（注意：容器必须为空才能删除）
    encoded_container_name = requests.utils.quote(container_name)  # 处理特殊字符
    url = f"http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665/{encoded_container_name}"
    response = requests.delete(url, headers=headers)

    # 根据响应状态处理
    if response.status_code == 204:  # 204表示删除成功
        return redirect('/containers')  # 删除成功后返回容器列表页
    elif response.status_code == 409:  # 409表示容器非空，无法删除
        return HttpResponse("删除失败：容器不为空，请先删除容器内的文件")
    else:
        return HttpResponse(f"删除容器失败，错误码: {response.status_code}")


def upload_file(request, container_name):
    if 'token' not in request.session:
        return redirect('/index')

    if request.method == 'POST' and request.FILES.get('myfile'):
        file = request.FILES['myfile']
        headers = {
            'X-Auth-Token': request.session['token'],
            'Content-Type': file.content_type
        }

        # 构造上传URL
        encoded_container = requests.utils.quote(container_name)
        encoded_filename = requests.utils.quote(file.name)
        url = f"http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665/{encoded_container}/{encoded_filename}"

        # 流式上传文件内容
        response = requests.put(url, data=file.chunks(), headers=headers)

        if response.status_code in [201, 202]:
            return redirect(f'/objects/{container_name}')
        else:
            return HttpResponse(f"文件上传失败，错误码: {response.status_code}")

    return redirect(f'/objects/{container_name}')


# 文件下载功能
def download_file(request, container_name, object_name):
    if 'token' not in request.session:
        return redirect('/index')

    headers = {
        'X-Auth-Token': request.session['token']
    }

    # 构造下载URL
    encoded_container = requests.utils.quote(container_name)
    encoded_object = requests.utils.quote(object_name)
    url = f"http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665/{encoded_container}/{encoded_object}"

    # 流式获取文件内容
    response = requests.get(url, headers=headers, stream=True)

    if response.status_code == 200:
        # 确定文件MIME类型
        content_type = response.headers.get('Content-Type', 'application/octet-stream')

        # 构建响应对象
        response = StreamingHttpResponse(
            streaming_content=response.iter_content(chunk_size=4096),
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{object_name}"'
        return response
    else:
        return HttpResponse(f"文件下载失败，错误码: {response.status_code}")


# 文件查看功能
def view_file(request, container_name, object_name):
    # 1. 验证用户登录状态
    if 'token' not in request.session:
        return redirect('/index')  # 未登录则跳转登录页

    # 2. 构建请求头（携带认证token）
    headers = {
        'X-Auth-Token': request.session['token'],
        'Accept': '*/*'  # 允许接收所有类型的响应
    }

    # 3. 处理URL编码（避免特殊字符导致的请求错误）
    try:
        encoded_container = requests.utils.quote(container_name, safe='')
        encoded_object = requests.utils.quote(object_name, safe='')
    except Exception as e:
        return HttpResponse(f"文件名编码错误：{str(e)}", status=400)

    # 4. 构建Swift服务的文件访问URL（替换为你的Swift服务地址）
    swift_base_url = "http://192.168.176.114:8080/v1/AUTH_e0c36a923a334919905c9877eb6fd665"
    url = f"{swift_base_url}/{encoded_container}/{encoded_object}"

    # 5. 向Swift服务请求文件内容（流式获取，适合大文件）
    try:
        # 禁用SSL验证（如果是http服务，可忽略；如果是https且证书无效，需添加verify=False）
        response = requests.get(url, headers=headers, stream=True, timeout=30)
    except requests.exceptions.RequestException as e:
        return HttpResponse(f"连接Swift服务失败：{str(e)}", status=500)

    # 6. 处理Swift服务的响应
    if response.status_code != 200:
        return HttpResponse(
            f"查看文件失败，Swift返回错误：{response.status_code} {response.reason}",
            status=response.status_code
        )

    # 7. 自动识别文件MIME类型（优先使用Swift返回的类型，其次自动猜测）
    content_type = response.headers.get('Content-Type')
    if not content_type:
        # 根据文件名猜测类型（如.pdf -> application/pdf）
        content_type, _ = mimetypes.guess_type(object_name)
        content_type = content_type or 'application/octet-stream'  # 默认二进制类型

    # 8. 区分展示类型：文本、图片、PDF等可直接在浏览器展示，其他类型提示下载
    if content_type.startswith(('text/', 'image/', 'application/pdf', 'application/json')):
        # 流式返回文件内容，直接在浏览器展示
        return StreamingHttpResponse(
            streaming_content=response.iter_content(chunk_size=4096),  # 分块传输
            content_type=content_type
        )
    else:
        # 非可展示类型，返回下载响应
        response = StreamingHttpResponse(
            streaming_content=response.iter_content(chunk_size=4096),
            content_type=content_type
        )
        response['Content-Disposition'] = f'attachment; filename="{object_name}"'
        return response