"""
Configuration loader for standards and accreditor configuration.
Integrates YAML configuration with the Python backend.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

@dataclass
class AccreditorStandard:
    """Represents a single accreditation standard."""
    id: str
    title: str
    category: str
    subcategory: str
    description: str
    evidence_requirements: List[str]

@dataclass
class Accreditor:
    """Represents an accrediting body."""
    name: str
    id: str
    full_name: str
    type: str
    region: str
    geographic_scope: List[str]
    standards_uri: str
    standards_version: str
    mapping_rules: str
    recognition_authority: str
    website: str
    applicable_institution_types: List[str]
    standards: List[AccreditorStandard]
    applicable_programs: Optional[List[str]] = None

@dataclass
class InstitutionType:
    """Represents an institution type."""
    id: str
    name: str
    description: str
    typical_accreditors: List[str]

@dataclass
class EvidenceTag:
    """Represents an evidence classification tag."""
    id: str
    category: str
    description: str
    keywords: List[str]

@dataclass
class MappingRule:
    """Represents mapping rule configuration."""
    description: str
    confidence_threshold: float
    requires_manual_review: bool
    evidence_multiplier: float

@dataclass
class AgentConfig:
    """Represents AI agent configuration."""
    model_preference: List[str]
    temperature: float
    max_tokens: int
    system_prompt: str

class StandardsConfigLoader:
    """Loads and manages standards configuration from YAML file."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize config loader with path to YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "standards_config.yaml"
        
        self.config_path = Path(config_path)
        self._config_data: Optional[Dict[str, Any]] = None
        self._accreditors: Optional[List[Accreditor]] = None
        self._institution_types: Optional[List[InstitutionType]] = None
        self._evidence_tags: Optional[List[EvidenceTag]] = None
        self._mapping_rules: Optional[Dict[str, MappingRule]] = None
        self._agent_configs: Optional[Dict[str, AgentConfig]] = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if self._config_data is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
        
        return self._config_data
    
    def get_accreditors(self) -> List[Accreditor]:
        """Get list of configured accreditors."""
        if self._accreditors is None:
            config = self._load_config()
            self._accreditors = []
            
            for acc_data in config.get('accreditors', []):
                standards = []
                for std_data in acc_data.get('standards', []):
                    standard = AccreditorStandard(
                        id=std_data['id'],
                        title=std_data['title'],
                        category=std_data['category'],
                        subcategory=std_data['subcategory'],
                        description=std_data['description'],
                        evidence_requirements=std_data['evidence_requirements']
                    )
                    standards.append(standard)
                
                accreditor = Accreditor(
                    name=acc_data['name'],
                    id=acc_data['id'],
                    full_name=acc_data['full_name'],
                    type=acc_data['type'],
                    region=acc_data['region'],
                    geographic_scope=acc_data['geographic_scope'],
                    standards_uri=acc_data['standards_uri'],
                    standards_version=acc_data['standards_version'],
                    mapping_rules=acc_data['mapping_rules'],
                    recognition_authority=acc_data['recognition_authority'],
                    website=acc_data['website'],
                    applicable_institution_types=acc_data['applicable_institution_types'],
                    standards=standards,
                    applicable_programs=acc_data.get('applicable_programs')
                )
                self._accreditors.append(accreditor)
        
        return self._accreditors
    
    def get_accreditor_by_id(self, accreditor_id: str) -> Optional[Accreditor]:
        """Get accreditor by ID."""
        accreditors = self.get_accreditors()
        return next((acc for acc in accreditors if acc.id == accreditor_id), None)
    
    def get_accreditors_by_region(self, region: str) -> List[Accreditor]:
        """Get accreditors by region."""
        accreditors = self.get_accreditors()
        return [acc for acc in accreditors if acc.region.lower() == region.lower()]
    
    def get_accreditors_by_type(self, accreditor_type: str) -> List[Accreditor]:
        """Get accreditors by type (regional, national, programmatic)."""
        accreditors = self.get_accreditors()
        return [acc for acc in accreditors if acc.type.lower() == accreditor_type.lower()]
    
    def get_accreditors_for_institution_type(self, institution_type: str) -> List[Accreditor]:
        """Get accreditors applicable to an institution type."""
        accreditors = self.get_accreditors()
        return [acc for acc in accreditors if institution_type in acc.applicable_institution_types]
    
    def get_institution_types(self) -> List[InstitutionType]:
        """Get list of configured institution types."""
        if self._institution_types is None:
            config = self._load_config()
            self._institution_types = []
            
            for inst_data in config.get('institution_types', []):
                institution_type = InstitutionType(
                    id=inst_data['id'],
                    name=inst_data['name'],
                    description=inst_data['description'],
                    typical_accreditors=inst_data['typical_accreditors']
                )
                self._institution_types.append(institution_type)
        
        return self._institution_types
    
    def get_institution_type_by_id(self, type_id: str) -> Optional[InstitutionType]:
        """Get institution type by ID."""
        institution_types = self.get_institution_types()
        return next((inst for inst in institution_types if inst.id == type_id), None)
    
    def get_evidence_tags(self) -> List[EvidenceTag]:
        """Get list of configured evidence tags."""
        if self._evidence_tags is None:
            config = self._load_config()
            self._evidence_tags = []
            
            for tag_data in config.get('evidence_tags', []):
                evidence_tag = EvidenceTag(
                    id=tag_data['id'],
                    category=tag_data['category'],
                    description=tag_data['description'],
                    keywords=tag_data['keywords']
                )
                self._evidence_tags.append(evidence_tag)
        
        return self._evidence_tags
    
    def get_evidence_tags_by_category(self, category: str) -> List[EvidenceTag]:
        """Get evidence tags by category."""
        evidence_tags = self.get_evidence_tags()
        return [tag for tag in evidence_tags if tag.category.lower() == category.lower()]
    
    def get_mapping_rules(self) -> Dict[str, MappingRule]:
        """Get mapping rules configuration."""
        if self._mapping_rules is None:
            config = self._load_config()
            self._mapping_rules = {}
            
            for rule_name, rule_data in config.get('mapping_rules', {}).items():
                mapping_rule = MappingRule(
                    description=rule_data['description'],
                    confidence_threshold=rule_data['confidence_threshold'],
                    requires_manual_review=rule_data['requires_manual_review'],
                    evidence_multiplier=rule_data['evidence_multiplier']
                )
                self._mapping_rules[rule_name] = mapping_rule
        
        return self._mapping_rules
    
    def get_mapping_rule(self, rule_name: str) -> Optional[MappingRule]:
        """Get specific mapping rule by name."""
        mapping_rules = self.get_mapping_rules()
        return mapping_rules.get(rule_name)
    
    def get_agent_configs(self) -> Dict[str, AgentConfig]:
        """Get AI agent configurations."""
        if self._agent_configs is None:
            config = self._load_config()
            self._agent_configs = {}
            
            for agent_name, agent_data in config.get('agent_config', {}).items():
                agent_config = AgentConfig(
                    model_preference=agent_data['model_preference'],
                    temperature=agent_data['temperature'],
                    max_tokens=agent_data['max_tokens'],
                    system_prompt=agent_data['system_prompt']
                )
                self._agent_configs[agent_name] = agent_config
        
        return self._agent_configs
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for specific agent."""
        agent_configs = self.get_agent_configs()
        return agent_configs.get(agent_name)
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._config_data = None
        self._accreditors = None
        self._institution_types = None
        self._evidence_tags = None
        self._mapping_rules = None
        self._agent_configs = None
    
    def get_standards_for_accreditor(self, accreditor_id: str) -> List[AccreditorStandard]:
        """Get standards for a specific accreditor."""
        accreditor = self.get_accreditor_by_id(accreditor_id)
        return accreditor.standards if accreditor else []
    
    def search_standards_by_keyword(self, keyword: str) -> List[tuple[Accreditor, AccreditorStandard]]:
        """Search standards by keyword in title or description."""
        results = []
        accreditors = self.get_accreditors()
        
        for accreditor in accreditors:
            for standard in accreditor.standards:
                if (keyword.lower() in standard.title.lower() or 
                    keyword.lower() in standard.description.lower() or
                    keyword.lower() in standard.category.lower() or
                    keyword.lower() in standard.subcategory.lower()):
                    results.append((accreditor, standard))
        
        return results
    
    def classify_evidence_by_keywords(self, text: str) -> List[EvidenceTag]:
        """Classify evidence text by matching keywords to tags."""
        text_lower = text.lower()
        matching_tags = []
        
        evidence_tags = self.get_evidence_tags()
        for tag in evidence_tags:
            for keyword in tag.keywords:
                if keyword.lower() in text_lower:
                    matching_tags.append(tag)
                    break  # Only add tag once even if multiple keywords match
        
        return matching_tags

# Global instance for easy access
standards_config = StandardsConfigLoader()
