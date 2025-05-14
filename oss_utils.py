from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import os
from qcloud_cos.cos_exception import CosClientError, CosServiceError

class TencentOss(): 
    def __init__(self): 
        SECRET_ID = 'AKIDpUv51h8JHyOYR3OTHp66pITN0NUKtWtz'
        SECRET_KEY = 'rSmqeCUYMt99sKVQ5VfwynU0LWUFqFUW'
        REGION = 'ap-guangzhou' 
        self.BUCKET = 'thingx-1326665451'
        config = CosConfig(Region=REGION, SecretId=SECRET_ID, SecretKey=SECRET_KEY)
        self.client = CosS3Client(config)

    def upload_file(self, local_file, cos_key):
        try:
            response = self.client.upload_file(
                Bucket=self.BUCKET,
                Key=cos_key,          # COS上的文件路径+文件名
                LocalFilePath=local_file  # 本地文件路径
            )
            print(f"文件上传成功：{response['ETag']}")
            return True
        except Exception as e:
            print(f"上传失败：{str(e)}")
            return False 

    def download_file(self, cos_key, local_file):
        try:
            response = self.client.download_file(
                Bucket=self.BUCKET,
                Key=cos_key,          # COS上的文件路径+文件名
                DestFilePath=local_file  # 本地保存路径
            )
            print("文件下载成功")
            return True
        except Exception as e:
            print(f"下载失败：{str(e)}")
            return False

    def create_folder(self, folder_path):
        """
        在 COS 中创建文件夹
        :param folder_path: 文件夹路径（如 "documents/2023/"）
        """
        try:
            # 关键：必须以 "/" 结尾，并上传一个 0 字节的空对象
            if not folder_path.endswith('/'):
                folder_path += '/'

            # 上传空对象（创建文件夹）
            response = self.client.put_object(
                Bucket=self.BUCKET,
                Key=folder_path,  # Key 必须以 / 结尾
                Body=b''          # 空内容
            )
            print(f"文件夹创建成功：{folder_path}")
            return True
        except CosClientError as e:
            print(f"客户端错误：{str(e)}")
            return False
        except CosServiceError as e:
            print(f"服务端错误：{e.get_error_code()}: {e.get_error_msg()}")
            return False

    def upload_folder(self, local_dir: str, cos_base_path: str) -> None:
            """
            把 local_dir（含子目录）整体传到 cos_base_path。
            只考虑 *nix 系统，假设路径分隔符都是 '/'。
            """
            local_dir = os.path.abspath(local_dir)            # 保守做绝对化

            for root, _, files in os.walk(local_dir):
                rel = os.path.relpath(root, local_dir)        # 相对路径
                cos_folder = cos_base_path if rel == '.' else f"{cos_base_path}/{rel}"

                if files:                                     # 有文件才建（空目录不管）
                    self.create_folder(f"{cos_folder}/")

                for fname in files:
                    local_file = os.path.join(root, fname)
                    cos_key    = f"{cos_folder}/{fname}"
                    self.upload_file(local_file, cos_key)

    def list_directory(self, target_path='', delimiter='/'):
        """
        列出指定路径下的所有文件和文件夹
        :param target_path: 目标路径（如 "documents/2023/"）
        :return: (文件列表, 文件夹列表)
        """
        target_path = target_path.lstrip('/')  # 标准化路径
        
        # 确保路径格式正确
        if target_path and not target_path.endswith('/'):
            target_path += '/'

        files = []
        folders = []
        marker = ''  # 分页标记
        is_truncated = True

        try:
            while is_truncated:
                response = self.client.list_objects(
                    Bucket=self.BUCKET,
                    Prefix=target_path,
                    Delimiter=delimiter,
                    Marker=marker
                )

                # 获取文件夹列表（CommonPrefixes）
                if 'CommonPrefixes' in response:
                    folders += [prefix['Prefix'] for prefix in response['CommonPrefixes']]

                # 获取文件列表（过滤掉文件夹标记）
                if 'Contents' in response:
                    for obj in response['Contents']:
                        key = obj['Key']
                        # 排除文件夹标记对象（大小为0且以/结尾）
                        if not (obj['Size'] == 0 and key.endswith('/')):
                            files.append({
                                'Key': key,
                                'Size': obj['Size'],
                                'LastModified': obj['LastModified']
                            })

                # 检查是否还有更多内容
                is_truncated = response.get('IsTruncated', 'false').lower() == 'true'
                marker = response.get('NextMarker', '') if is_truncated else ''

            return files, folders

        except CosServiceError as e:
            print(f"请求失败：{e.get_error_code()} - {e.get_error_msg()}")
            return [], []

    def get_oss_url(self, key, expired=3600):
        url = self.client.get_presigned_download_url(
            Bucket=self.BUCKET,
            Key=key,
            Expired=expired  # 有效期（秒），最大 7 天（604800 秒）
        )
        return url