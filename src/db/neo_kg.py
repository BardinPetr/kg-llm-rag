from neomodel import StringProperty

from utils.file import do_hash
from db.neo_base import CodedNode
from db.neo_rel_prop import RelationshipFrom, RelationshipTo
from db.neo_doc import DEmbeddable, DBlock, MentionedInRel, ProvedByRel


class KType(CodedNode):
    pass


class KFactType(CodedNode):
    pass


class KNode(DEmbeddable):
    uid = StringProperty(required=True, unique_index=True)
    described_with = RelationshipFrom("KFact", "K_SUBJ")


class KEntity(KNode):
    type = RelationshipTo[KType](KType, "K_IS")
    type_code = StringProperty()
    mentions = RelationshipTo[DBlock](DBlock, "K_MENTION", model=MentionedInRel)
    object_of = RelationshipFrom("KFact", "K_OBJ")

    def __str__(self):
        return f"{self.uid}:{self.type_code}(`{self.repr}`)"

    def __repr__(self):
        return str(self)

    @classmethod
    def hash(cls, name) -> str:
        return do_hash(name)


class KFact(KNode):
    type = RelationshipTo[KFactType](KFactType, "K_IS")
    type_code = StringProperty()
    proof = RelationshipTo[DBlock](DBlock, "K_PROOF", model=ProvedByRel)
    subject = RelationshipTo[KNode](KNode, "K_SUBJ")
    objects = RelationshipTo[KNode](KNode, "K_OBJ")

    def __str__(self):
        return f"FCT:{self.type_code}({self.repr[:50]})"

    def __repr__(self):
        return str(self)


class KRelFact(KFact):
    def __str__(self):
        subj = self.subject.all()
        subj = str(subj[0]) if subj else "X"
        objs = [str(i) for i in self.objects.all()]
        objs = ";".join(objs)
        objs = f"[{objs}]"
        data = [str(i) for i in self.described_with if isinstance(i, KValFact)]
        data = ";".join(data)
        return f"{subj}--{self.uid}:{self.type_code}({data})-->{objs}"

    def __repr__(self):
        return str(self)


class KValFact(KFact):
    value = StringProperty(required=True)
    unit = StringProperty()  # TODO

    def __str__(self):
        return f"{self.uid}:{self.type_code}=`{self.value}`{self.unit or ''}"

    def __repr__(self):
        return str(self)
