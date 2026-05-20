from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from core.Database import Base

class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    cargo = Column(String, default='comum')
    data_criacao = Column(DateTime, default=datetime.utcnow)

    # Relacionamento: Um usuário pode ter criado várias demandas e feito várias edições
    demandas_criadas = relationship("DemandaModel", back_populates="criador")
    historico_alteracoes = relationship("HistoricoEdicoesModel", back_populates="usuario")


class DemandaModel(Base):
    __tablename__ = "demandas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=False)
    solicitante = Column(String, nullable=False)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    prioridade = Column(String, default='Media')
    status = Column(String, default='Aberta')
    data_conclusao = Column(DateTime, nullable=True)
    prazo = Column(DateTime, nullable=True)
    criado_por = Column(Integer, ForeignKey('usuarios.id'), nullable=True)

    # Relacionamentos com as outras tabelas
    criador = relationship("UsuarioModel", back_populates="demandas_criadas")
    comentarios = relationship("ComentarioModel", back_populates="demanda", cascade="all, delete-orphan")
    historico = relationship("HistoricoEdicoesModel", back_populates="demanda", cascade="all, delete-orphan")


class ComentarioModel(Base):
    __tablename__ = "comentarios"

    id = Column(Integer, primary_key=True, index=True)
    demanda_id = Column(Integer, ForeignKey('demandas.id'), nullable=False)
    comentario = Column(Text, nullable=False)
    autor = Column(String, nullable=False)
    data = Column(DateTime, default=datetime.utcnow)

    demanda = relationship("DemandaModel", back_populates="comentarios")


class HistoricoEdicoesModel(Base):
    __tablename__ = "historico_edicoes"

    id = Column(Integer, primary_key=True, index=True)
    demanda_id = Column(Integer, ForeignKey('demandas.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    data = Column(DateTime, default=datetime.utcnow, nullable=False)
    campo_alterado = Column(String, nullable=False)
    valor_anterior = Column(Text, nullable=True)
    valor_novo = Column(Text, nullable=True)

    # Relacionamentos
    demanda = relationship("DemandaModel", back_populates="historico")
    usuario = relationship("UsuarioModel", back_populates="historico_alteracoes")