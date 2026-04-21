from abc import abstractmethod
from typing import Optional, Protocol

from workspace.extract.full.datastore.s3store import S3ObjectStore


class ObjectStore(Protocol):

    @abstractmethod
    def exists(self, group: str, name: str) -> bool: ...

    @abstractmethod
    def store(self, group: str, name: str, data: bytes) -> bool: ...

    @abstractmethod
    def load(self, group: str, name: str) -> Optional[bytes]: ...

    @abstractmethod
    def delete(self, group: str, name: str) -> bool: ...


default_store = S3ObjectStore()
