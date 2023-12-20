from sqlalchemy import Float
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class monitor(Base):
    __tablename__ = 'monitor'
    
    nama_monitor: Mapped[str] = mapped_column(primary_key=True)
    reputasi_brand: Mapped[int] = mapped_column()
    refresh_rate: Mapped[int] = mapped_column()
    resolusi: Mapped[int] = mapped_column()
    harga: Mapped[int] = mapped_column()
    ukuran_layar: Mapped[int] = mapped_column()
    
    def __repr__(self) -> str:
        return f"monitor(nama_monitor={self.nama_monitor!r}, reputasi_brand={self.reputasi_brand!r})"