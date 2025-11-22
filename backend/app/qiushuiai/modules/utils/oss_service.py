"""
阿里云 OSS 文件上传服务

提供文件上传到阿里云 OSS 的功能，支持:
- 普通文件上传
- 大文件分片上传 (multipart upload)
- 自动生成 UUID 文件名
- 按年/月组织文件路径
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

import oss2
from oss2.models import PartInfo
from oss2.exceptions import ClientError

from qiushuiai.core.config import settings


class OSSService:
    """阿里云 OSS 上传服务"""

    def __init__(self) -> None:
        """初始化 OSS 客户端"""
        # 检查必要的配置
        if not settings.OSS_BUCKET_NAME or not settings.OSS_BUCKET_NAME.strip():
            raise ValueError(
                "OSS_BUCKET_NAME 未配置或为空，请在环境变量或 .env 文件中设置有效的 OSS_BUCKET_NAME"
            )
        if not settings.OSS_ACCESS_KEY_ID or not settings.OSS_ACCESS_KEY_ID.strip():
            raise ValueError(
                "OSS_ACCESS_KEY_ID 未配置或为空，请在环境变量或 .env 文件中设置有效的 OSS_ACCESS_KEY_ID"
            )
        if not settings.OSS_ACCESS_KEY_SECRET or not settings.OSS_ACCESS_KEY_SECRET.strip():
            raise ValueError(
                "OSS_ACCESS_KEY_SECRET 未配置或为空，请在环境变量或 .env 文件中设置有效的 OSS_ACCESS_KEY_SECRET"
            )
        
        auth = oss2.Auth(
            settings.OSS_ACCESS_KEY_ID,
            settings.OSS_ACCESS_KEY_SECRET
        )
        try:
            self.bucket = oss2.Bucket(
                auth,
                settings.OSS_ENDPOINT,
                settings.OSS_BUCKET_NAME
            )
        except ClientError as e:
            raise ValueError(
                f"OSS 初始化失败: {str(e)}。请检查以下配置是否正确：\n"
                f"- OSS_BUCKET_NAME: {settings.OSS_BUCKET_NAME}\n"
                f"- OSS_ENDPOINT: {settings.OSS_ENDPOINT}\n"
                f"- OSS_ACCESS_KEY_ID: {'已设置' if settings.OSS_ACCESS_KEY_ID else '未设置'}\n"
                f"- OSS_ACCESS_KEY_SECRET: {'已设置' if settings.OSS_ACCESS_KEY_SECRET else '未设置'}"
            ) from e

    def generate_oss_path(self, original_filename: str) -> str:
        """
        生成 OSS 存储路径

        格式: uploads/{year}/{month}/{uuid}.{ext}
        例如: uploads/2025/10/a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf

        Args:
            original_filename: 原始文件名

        Returns:
            OSS 对象路径
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")

        # 提取文件扩展名
        ext = Path(original_filename).suffix

        # 生成 UUID 文件名
        file_uuid = str(uuid.uuid4())
        filename = f"{file_uuid}{ext}"

        # 组合完整路径
        oss_path = f"uploads/{year}/{month}/{filename}"

        return oss_path

    def upload_file(
        self,
        file_obj: BinaryIO,
        original_filename: str,
        file_size: int
    ) -> str:
        """
        上传文件到 OSS

        根据文件大小自动选择普通上传或分片上传

        Args:
            file_obj: 文件对象
            original_filename: 原始文件名
            file_size: 文件大小(字节)

        Returns:
            OSS 文件 URL

        Raises:
            oss2.exceptions.OssError: OSS 操作失败
        """
        oss_path = self.generate_oss_path(original_filename)

        if file_size >= settings.MULTIPART_THRESHOLD:
            # 大文件使用分片上传
            self._multipart_upload(file_obj, oss_path, file_size)
        else:
            # 小文件使用普通上传
            self.bucket.put_object(oss_path, file_obj)

        # 生成公共读 URL
        url = self.get_public_url(oss_path)

        return url

    def _multipart_upload(
        self,
        file_obj: BinaryIO,
        oss_path: str,
        file_size: int
    ) -> None:
        """
        分片上传大文件

        Args:
            file_obj: 文件对象
            oss_path: OSS 对象路径
            file_size: 文件大小(字节)

        Raises:
            oss2.exceptions.OssError: OSS 操作失败
        """
        # 初始化分片上传
        upload_id = self.bucket.init_multipart_upload(oss_path).upload_id

        parts = []
        part_number = 1
        offset = 0

        try:
            while offset < file_size:
                # 计算本次上传的分片大小
                num_to_upload = min(settings.PART_SIZE, file_size - offset)

                # 读取分片数据
                file_obj.seek(offset)
                chunk = file_obj.read(num_to_upload)

                # 上传分片
                result = self.bucket.upload_part(
                    oss_path,
                    upload_id,
                    part_number,
                    chunk
                )

                # 记录分片信息
                parts.append(PartInfo(part_number, result.etag))

                offset += num_to_upload
                part_number += 1

            # 完成分片上传
            self.bucket.complete_multipart_upload(
                oss_path,
                upload_id,
                parts
            )

        except Exception as e:
            # 上传失败,取消分片上传
            self.bucket.abort_multipart_upload(oss_path, upload_id)
            raise e

    def get_public_url(self, oss_path: str) -> str:
        """
        获取文件的公共访问 URL

        Args:
            oss_path: OSS 对象路径

        Returns:
            公共访问 URL
        """
        # 对于公共读的 bucket,直接拼接 URL
        # 格式: https://{bucket}.{endpoint}/{path}
        url = f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{oss_path}"

        return url

    def delete_file(self, oss_path: str) -> None:
        """
        删除 OSS 文件

        Args:
            oss_path: OSS 对象路径

        Raises:
            oss2.exceptions.OssError: OSS 操作失败
        """
        self.bucket.delete_object(oss_path)

    def file_exists(self, oss_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            oss_path: OSS 对象路径

        Returns:
            文件是否存在
        """
        return self.bucket.object_exists(oss_path)


# 懒加载单例模式
class _OSSServiceProxy:
    """
    OSS 服务代理类，实现懒加载
    只有在实际使用时才初始化 OSS 服务
    """
    
    def __init__(self):
        self._instance: OSSService | None = None
    
    def _get_instance(self) -> OSSService:
        """获取实际的服务实例（懒加载）"""
        if self._instance is None:
            self._instance = OSSService()
        return self._instance
    
    def __getattr__(self, name: str):
        """代理所有属性访问到实际的服务实例"""
        return getattr(self._get_instance(), name)


# 创建代理实例，实现懒加载
# 这样在模块导入时不会立即初始化 OSS 服务
# 只有在实际使用时才会初始化
oss_service = _OSSServiceProxy()
