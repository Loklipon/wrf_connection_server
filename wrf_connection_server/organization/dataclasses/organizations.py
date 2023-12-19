from pydantic import BaseModel, Field


class OrganizationUnit(BaseModel):
    uuid: str = Field(alias='id')
    name: str


class OrganizationUnitsList(BaseModel):
    organizations: list[OrganizationUnit]


class Terminal(BaseModel):
    uuid: str = Field(alias='id')
    org_unit_uuid: str = Field(alias='organizationId')
    name: str


class TerminalGroup(BaseModel):
    terminals: list[Terminal] = Field(alias='items')


class TerminalGroupsList(BaseModel):
    terminal_groups: list[TerminalGroup] = Field(alias='terminalGroups')